"""
Stream file in real time in order to simulate live speech.
"""
import argparse
import os
import time
from threading import Thread

import requests
import websocket as ws  # type: ignore
from websocket import WebSocketTimeoutException  # type: ignore

from uhlive.auth import build_authentication_request
from uhlive.stream.conversation import Conversation, Ok, build_conversation_url


class AudioSender(Thread):
    def __init__(self, socket, client, audio_file, codec):
        Thread.__init__(self)
        self.socket = socket
        self.client = client
        self.audio_file = audio_file
        self.chunk_size = 4000 if codec.startswith("g711") else 8000

    def run(self):
        print(f"Streaming file in realtime: {self.audio_file} for transcription!")
        with open(self.audio_file, "rb") as audio_file:
            while True:
                audio_chunk = audio_file.read(self.chunk_size)
                if not audio_chunk:
                    break
                self.socket.send_binary(self.client.send_audio_chunk(audio_chunk))
                time.sleep(0.5)

        print(f"File {self.audio_file} successfully streamed")
        self.socket.send(self.client.leave())


parser = argparse.ArgumentParser(
    description="Get the transcription of an audio file, live!"
)
parser.add_argument("audio_file", help="Audio file to transcribe")
parser.add_argument("conversation_id", help="Conversation ID")
parser.add_argument("--asr_model", dest="model", default="fr")
parser.add_argument("--audio_codec", dest="codec", default="linear")
parser.add_argument("--country", dest="country", default="fr")
parser.add_argument(
    "--without_interim_results",
    dest="interim_results",
    action="store_false",
)
parser.add_argument("--without_rescoring", dest="rescoring", action="store_false")
args = parser.parse_args()

uhlive_client = os.environ["UHLIVE_API_CLIENT"]
uhlive_secret = os.environ["UHLIVE_API_SECRET"]

auth_url, auth_params = build_authentication_request(uhlive_client, uhlive_secret)
login = requests.post(auth_url, data=auth_params)
login.raise_for_status()
uhlive_token = login.json()["access_token"]

url = build_conversation_url(uhlive_token)
socket = ws.create_connection(url, timeout=10)
client = Conversation(uhlive_client, args.conversation_id, "Alice")

socket.send(
    client.join(
        model=args.model,
        interim_results=args.interim_results,
        rescoring=args.rescoring,
        origin=int(time.time() * 1000),
        country=args.country,
        audio_codec=args.codec,
    )
)
join = time.time()
# check we didn't get an error on join
data = socket.recv()
print("join resp =", client.receive(data), "in", time.time() - join, "seconds")


sender = AudioSender(socket, client, args.audio_file, args.codec)
sender.start()


print("Listening to events")
try:
    while True:
        try:
            event = client.receive(socket.recv())
        except WebSocketTimeoutException:
            print("Silence")
            continue
        if client.left:
            print("Transcription completed")
            break
        elif not isinstance(event, Ok):
            print(event)
finally:
    print("Exiting")
    sender.join()
    socket.close()
