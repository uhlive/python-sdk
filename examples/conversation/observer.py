"""
Get the events of an ongoing conversation.
"""
import argparse
import os
from time import time

import requests
import websocket as ws  # type: ignore
from websocket import WebSocketTimeoutException  # type: ignore

from uhlive.auth import build_authentication_request
from uhlive.stream.conversation import Conversation, Ok, build_conversation_url

parser = argparse.ArgumentParser(
    description="Get the events of an ongoing conversation."
)
parser.add_argument("conversation_id", help="Conversation ID")
args = parser.parse_args()

uhlive_client = os.environ["UHLIVE_API_CLIENT"]
uhlive_secret = os.environ["UHLIVE_API_SECRET"]

auth_url, auth_params = build_authentication_request(uhlive_client, uhlive_secret)
login = requests.post(auth_url, data=auth_params)
login.raise_for_status()
uhlive_token = login.json()["access_token"]

url = build_conversation_url(uhlive_token)
socket = ws.create_connection(url, timeout=10)
client = Conversation(uhlive_client, args.conversation_id, "observer")

socket.send(client.join(readonly=True))

print("Listening to events")
last_ping = time()
try:
    while True:
        # As we don't stream audio, we need to regularly ping the server to keep the connection open
        if time() - last_ping > 15:
            socket.ping()
            last_ping = time()
        try:
            event = client.receive(socket.recv())
        except WebSocketTimeoutException:
            print("Silence")
            continue
        if isinstance(event, Ok):
            continue
        else:
            print(event)
finally:
    print("Exiting")
    socket.send(client.leave())
    socket.close()
