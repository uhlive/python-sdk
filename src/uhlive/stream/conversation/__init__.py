"""
The Stream Conversation SDK API for human to human interactions.

This API is used to consume a real-time audio stream and get enriched transcription events.
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
    "build_conversation_url",
]
