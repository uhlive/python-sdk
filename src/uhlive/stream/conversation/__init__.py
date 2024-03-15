"""
The Stream Conversation SDK API for human to human interactions.

This API is used to consume a real-time audio stream and get enriched transcription events.

The protocol is messages based and uses websockets as transport. You are free to use whatever websocket client library you like to communicate
with the API, and use our SDK to encode/decode the messages.

## Quickstart

First retrieve a one time access token with the [Auth API](auth.md).

Then use that token to build an authenticated URL, open a websocket connection to it with the websocket client library
of your choice and instanciate a [`Conversation`][uhlive.stream.conversation.Conversation] to join a conversation, generate
audio stream messages and decode transcription and enrichment events.

As the API is asynchronous, streaming the audio and reading the returned events should be done in two different threads/tasks.

```python
from uhlive.stream.Conversation import *

stream_h2h_url = build_conversation_url(token)

# The subcripttion identifier was given to you with your other credentials
# the conversation id can be any string you like. If a conversation by that name already exists in your subscription identifier domain
# it will join it as a new speaker, otherwise it will create it and join the speaker in.
# The speaker id helps you identify who is speaking.
conversation = Conversation("subscription_identifier", "a_conversation_id", "a_speaker_id")
```

Now you can connect and interact with the API:

Synchronous example:

```python
import websocket as ws

socket = ws.create_connection(stream_h2h_url, timeout=10)
socket.send(
    conversation.join(
        model="fr",
        interim_results=False,
        rescoring=True,
        origin=int(time.time() * 1000),
        country="fr",
    )
)
# check we didn't get an error on join
reply = conversation.receive(socket.recv())
assert isinstance(reply, Ok)

```

Asynchronous example:

```python
from aiohttp import ClientSession

async def main(uhlive_client, uhlive_secret):
    async with ClientSession() as session:
        async with session.ws_connect(stream_h2h_url) as socket:
            await socket.send_str(
                conversation.join(
                    model="fr",
                    interim_results=False,
                    rescoring=True,
                    origin=int(time.time() * 1000),
                    country="fr",
                )
            )
            # check we didn't get an error on join
            msg = await socket.receive()
            reply = conversation.receive(msg.data)
            assert isinstance(reply, Ok)
```

As you can see, the I/O is cleanly decoupled from the protocol handling: the `Conversation` object is only used
to create the messages to send to the API and to decode the received messages as `Event` objects.

See the [complete examples in the source distribution](https://github.com/uhlive/python-sdk/tree/main/examples/conversation).
"""

import os
from urllib.parse import urljoin

from .client import Conversation, ProtocolError
from .events import (
    EntityFound,
    EntityReference,
    Event,
    Ok,
    RelationFound,
    SegmentDecoded,
    SpeakerJoined,
    SpeakerLeft,
    SpeechDecoded,
    Tag,
    TagsFound,
    Unknown,
    Word,
    WordsDecoded,
)

SERVER = os.getenv("UHLIVE_API_URL", "wss://api.uh.live")


def build_conversation_url(token: str) -> str:
    """
    Make an authenticated URL to connect to the Conversation Service.
    """
    return urljoin(SERVER, "socket/websocket") + f"?jwt={token}&vsn=2.0.0"


__all__ = [
    "build_conversation_url",
    "Conversation",
    "ProtocolError",
    "SpeakerJoined",
    "Word",
    "EntityFound",
    "Event",
    "Ok",
    "EntityReference",
    "RelationFound",
    "SegmentDecoded",
    "SpeakerLeft",
    "SpeechDecoded",
    "Unknown",
    "WordsDecoded",
    "Tag",
    "TagsFound",
]
