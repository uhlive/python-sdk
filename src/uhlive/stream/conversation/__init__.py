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


def build_conversation_url(base_url, token):
    return urljoin(base_url, "socket/websocket") + f"?token={token}&vsn=2.0.0"
