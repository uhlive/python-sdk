import os
from urllib.parse import urljoin

from .client import Conversation, ProtocolError  # noqa
from .events import (  # noqa
    EntityFound,
    Event,
    Ok,
    RelationFound,
    SegmentDecoded,
    SpeakerLeft,
    SpeechDecoded,
    Unknown,
    WordsDecoded,
)

SERVER = os.getenv("UHLIVE_API_URL", "wss://api.uh.live")


def build_conversation_url(token):
    return urljoin(SERVER, "socket/websocket") + f"?jwt={token}&vsn=2.0.0"
