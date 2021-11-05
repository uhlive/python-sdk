"""
Stream file in real time in order to simulate live speech.
"""
import argparse
import os
import time
from threading import Thread

import websocket as ws  # type: ignore
from websocket import WebSocketTimeoutException  # type: ignore

from uhlive.stream.conversation import Conversation, Ok, build_conversation_url


class AudioSender(Thread):
    def __init__(self, socket, client, audio_file):
        Thread.__init__(self)
        self.socket = socket
        self.client = client
        self.audio_file = audio_file

    def run(self):
        print(f"Streaming file in realtime: {self.audio_file} for transcription!")
        with open(self.audio_file, "rb") as audio_file:
            while True:
                audio_chunk = audio_file.read(8000)
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
parser.add_argument("--country", dest="country", default="fr")
parser.add_argument(
    "--without_interim_results",
    dest="interim_results",
    action="store_false",
)
parser.add_argument("--without_rescoring", dest="rescoring", action="store_false")
args = parser.parse_args()

uhlive_url = os.environ["UHLIVE_API_URL"]
uhlive_token = os.environ["UHLIVE_API_TOKEN"]
uhlive_id = os.environ["UHLIVE_API_ID"]

url = build_conversation_url(uhlive_url, uhlive_token)
socket = ws.create_connection(url, timeout=10)

client = Conversation(uhlive_id, args.conversation_id, "Alice")

socket.send(
    client.join(
        model=args.model,
        interim_results=args.interim_results,
        rescoring=args.rescoring,
        origin=int(time.time() * 1000),
        country=args.country,
    )
)
# check we didn't get an error on join
client.receive(socket.recv())


sender = AudioSender(socket, client, args.audio_file)
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
