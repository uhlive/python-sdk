"""
The stream recognition API SDK for voice bots.

Stream for voicebots, or Stream Human to Bots, or Stream H2B is a set of API enabling clients to build
interaction between a human end-user and a bot, for example to create Interactive Voice Response (IVR)
on the phone, or a voicebot within an app.

For an overview of the concepts, protocols and workflow, see the
[higher level documenation](https://docs.allo-media.net/stream-h2b/#real-time-stream-api-for-voicebots) and
more specifically the [Websocket H2B protocol reference](https://docs.allo-media.net/stream-h2b/protocols/websocket/#websocket-for-voicebots).

The protocol is messages based and uses websockets as transport. You are free to use whatever websocket client library you like to communicate
with the API, and use our SDK to encode/decode the messages.

## Quickstart

First retrieve a one time access token with the [Auth API](auth.md).

Then use that token to build an authenticated URL, open a websocket connection to it with the websocket client library
of your choice and instanciate a [`Recognizer`][uhlive.stream.recognition.Recognizer] to make request, generate
audio stream messages and decode responses.

As the API is asynchronous, streaming the audio and reading the returned events should be done in two different threads/tasks.

```python
from uhlive.stream.recognition import *

stream_h2b_url, stream_h2b_headers = build_connection_request(token)
recognizer = Recognizer()
```

Now you can connect and interact with the API:

Synchronous example:

```python
import websocket as ws

socket = ws.create_connection(stream_h2b_url, header=stream_h2b_headers)
socket.send(recognizer.open())
# Check if successful
reply = recognizer.receive(socket.recv())
assert isinstance(reply, Opened), f"Expected Opened, got {reply}"
# start streaming the user's voice in another thread
streamer_thread_handle = stream_mic(socket, recognizer)
```

Asynchronous example:

```python
from aiohttp import ClientSession

    async with ClientSession() as session:
        async with session.ws_connect(stream_h2b_url, header=stream_h2b_headers) as socket:

            # Open a session
            # Commands are sent as text frames
            await socket.send_str(recognizer.open())
            # Check if successful
            msg = await socket.receive()
            reply = recognizer.receive(msg.data)
            assert isinstance(reply, Opened), f"Expected Opened, got {reply}"
            # start streaming the user's voice in another task
            streamer_task_handle = asyncio.create_task(stream(socket, recognizer))
```

As you can see, the I/O is cleanly decoupled from the protocol handling: the `Recognizer` object is only used
to create the messages to send to the API and to decode the received messages as `Event` objects.

See the [complete examples in the source distribution](https://github.com/uhlive/python-sdk/tree/main/examples/recognition).

"""

import os
from typing import Tuple
from urllib.parse import urljoin

from .client import ProtocolError, Recognizer
from .events import (
    Closed,
    CompletionCause,
    DefaultParams,
    Event,
    GrammarDefined,
    InputTimersStarted,
    Interpretation,
    InvalidParamValue,
    MethodFailed,
    MethodNotAllowed,
    MethodNotValid,
    MissingParam,
    Opened,
    ParamsSet,
    RecognitionComplete,
    RecognitionInProgress,
    RecogResult,
    StartOfInput,
    Stopped,
    Transcript,
)

SERVER = os.getenv("UHLIVE_API_URL", "wss://api.uh.live")


def build_connection_request(token) -> Tuple[str, dict]:
    """
    Make an authenticated URL and header to connect to the H2B Service.
    """
    return urljoin(SERVER, "/bots"), {"Authorization": f"bearer {token}"}


__all__ = [
    "ProtocolError",
    "Recognizer",
    "build_connection_request",
    "Event",
    "CompletionCause",
    "Transcript",
    "Interpretation",
    "RecogResult",
    "Opened",
    "ParamsSet",
    "DefaultParams",
    "GrammarDefined",
    "RecognitionInProgress",
    "InputTimersStarted",
    "Stopped",
    "Closed",
    "StartOfInput",
    "RecognitionComplete",
    "MethodNotValid",
    "MethodFailed",
    "InvalidParamValue",
    "MissingParam",
    "MethodNotAllowed",
]
