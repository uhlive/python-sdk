import argparse
import os
import time

import requests
import sounddevice as sd  # type: ignore
import websocket as ws  # type: ignore
from websocket import WebSocketTimeoutException  # type: ignore

from uhlive.auth import build_authentication_request
from uhlive.stream.conversation import Conversation, Ok, build_conversation_url

# Audio recording parameters
RATE = 8000
CHUNK = int(RATE / 10)  # 100ms


def stream_microphone(socket, client):
    def callback(indata, frame_count, time_info, status):
        socket.send_binary(client.send_audio_chunk(bytes(indata)))

    stream = sd.RawInputStream(
        callback=callback, channels=1, samplerate=8000, dtype="int16", blocksize=960
    )
    stream.start()
    return stream


parser = argparse.ArgumentParser(
    description="Get the transcription of an audio file, live!"
)
parser.add_argument("conversation_id", help="Conversation ID")
parser.add_argument("--asr_model", dest="model", default="fr")
parser.add_argument("--country", dest="country", default="fr")
parser.add_argument(
    "--without_interim_results",
    dest="interim_results",
    action="store_false",
)
parser.add_argument("--without_rescoring", dest="rescoring", action="store_false")
parser.add_argument("--user", dest="user_id", default="")
parser.add_argument("--password", dest="user_pwd", default="")
args = parser.parse_args()

uhlive_client = os.environ["UHLIVE_API_CLIENT"]
uhlive_secret = os.environ["UHLIVE_API_SECRET"]

auth_url, auth_params = build_authentication_request(
    uhlive_client, uhlive_secret, args.user_id, args.user_pwd
)
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
    )
)
# check we didn't get an error on join
client.receive(socket.recv())

stream = stream_microphone(socket, client)

print("Listening to events")
try:
    while True:
        try:
            event = client.receive(socket.recv())
        except WebSocketTimeoutException:
            print("— Silence —")
            continue
        except KeyboardInterrupt:
            break
        if not isinstance(event, Ok):
            print(event)
finally:
    print("Exiting")
    stream.stop()
    stream.close()
    socket.send(client.leave())
    socket.close()
