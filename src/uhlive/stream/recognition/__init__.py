"""
The stream recognition API SDK for voice bots.

Stream for voicebots, or Stream Human to Bots, or Stream H2B is a set of API enabling clients to build
interaction between a human end-user and a bot, for example to create Interactive Voice Response (IVR)
on the phone, or a voicebot within an app.

For an overview of the concepts, protocols and workflow, see the
[higher level documenation](https://docs.allo-media.net/stream-h2b/#real-time-stream-api-for-voicebots) and
more specifically the [Websocket H2B protocol reference](https://docs.allo-media.net/stream-h2b/protocols/websocket/#websocket-for-voicebots).
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
