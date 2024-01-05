"""Event definitions."""

import re
from typing import Any, List

from .error import UhliveError
from .human_datetime import human_datetime

ENTITY_NAME = re.compile(r"entity_([\w_]+)_found")
RELATION_NAME = re.compile(r"relation_([\w_]+)_found")


class Word(dict):
    """Timestamped word."""

    @property
    def start(self) -> int:
        """Start time as Unix timestamp in millisecond, according to audio timeline."""
        return self["start"]

    @property
    def end(self) -> int:
        """End time as Unix timestamp in millisecond, according to audio timeline."""
        return self["end"]

    @property
    def length(self) -> int:
        """Word length in millisecond, according to audio timeline."""
        return self["length"]

    @property
    def word(self) -> str:
        """Transcript token string for this word."""
        return self["word"]

    @property
    def confidence(self) -> float:
        """ASR confidence for this word."""
        return self["confidence"]


class Event(object):
    """The base class of all events."""

    def __init__(self, join_ref, ref, topic, event, payload) -> None:
        self._join_ref = join_ref
        self._ref = ref
        self._topic = topic
        self._payload = payload

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(payload={self._payload})"

    @property
    def topic(self) -> str:
        """The conversation identifier"""
        return self._topic

    @property
    def join_ref(self) -> str:
        return self._join_ref

    @property
    def ref(self) -> str:
        return self._ref

    @property
    def speaker(self) -> str:
        """The speaker whose speech triggered this event.

        All events are relative to a speaker."""
        return self._payload["speaker"]

    @staticmethod
    def from_message(message):
        """Private method to instantiate the right type of event from the raw websocket message."""
        [join_ref, ref, topic, event, payload] = message
        if event == "phx_reply" and payload["status"] == "error":
            raise UhliveError(payload["response"]["reason"])
        if event in EVENT_MAP:
            return EVENT_MAP[event](*message)
        if event.startswith("entity_"):
            return EntityFound(*message)
        if event.startswith("relation_"):
            return RelationFound(*message)
        if event == "phx_error":
            raise UhliveError("Server error, channel crashed!")
        return Unknown(*message)


class Ok(Event):
    """API asynchronous command aknowledgements."""

    pass


class Unknown(Event):
    """The server emitted an event unkown to this SDK. Time to upgrade!"""

    def __init__(self, join_ref, ref, topic, event, payload):
        self._name = event
        super().__init__(join_ref, ref, topic, event, payload)

    def __repr__(self) -> str:
        return f"Unknown [{self._name}](payload={self._payload})"


class TimeScopedEvent(Event):
    """Base class for events that are anchored to the audio time line."""

    @property
    def start(self) -> int:
        """Start time as Unix timestamp in millisecond, according to audio timeline."""
        return self._payload["start"]

    @property
    def end(self) -> int:
        """End time as Unix timestamp in millisecond, according to audio timeline."""
        return self._payload["end"]

    @property
    def length(self) -> int:
        """Event length in millisecond, according to audio timeline."""
        return self._payload["length"]


class SpeechDecoded(TimeScopedEvent):
    """The base class of all transcription events."""

    @property
    def transcript(self) -> str:
        """Get the transcript of the whole segment as a string"""
        return self._payload["transcript"]

    @property
    def lang(self) -> str:
        """Natural Language of the speech.

        As ISO 639-1 code.
        """
        return self._payload["lang"]

    @property
    def country(self) -> str:
        """Country location of speaker.

        As ISO 3166-1 code.
        """
        return self._payload["country"]

    @property
    def utterance_id(self) -> str:
        """The Utterance id identifies the speech utterance this event transcribes."""
        return self._payload["utterance_id"]

    @property
    def words(self) -> List[Word]:
        """Get the transcript of the whole segment as a list of timestamped [words][uhlive.stream.conversation.Word]."""
        return [Word(w) for w in self._payload["words"]]

    def __str__(self) -> str:
        return f"[{self.speaker} — {human_datetime(self.start)}] {self.transcript}"

    @property
    def confidence(self) -> float:
        """The ASR confidence for this segment."""
        return self._payload["confidence"]


class WordsDecoded(SpeechDecoded):
    """Interim segment transcript event."""

    pass


class SegmentDecoded(SpeechDecoded):
    """Final segment transcript event."""

    pass


class SegmentNormalized(SpeechDecoded):
    """Normalized final segment event."""

    def __str__(self) -> str:
        return f"[{self.speaker} — Formatted] {self.transcript}"


class SpeakerJoined(Event):
    """A new speaker joined the conversation (after us)."""

    @property
    def timestamp(self) -> int:
        """The UNIX time when the speaker joined the conversation."""
        return self._payload["timestamp"]

    @property
    def interim_results(self) -> bool:
        """Are interim results activated for this speaker?"""
        return self._payload["interim_results"]

    @property
    def rescoring(self) -> bool:
        """Is rescoring enabled for this speaker?"""
        return self._payload["rescoring"]

    @property
    def lang(self) -> str:
        """Natural Language of the speech.

        As ISO 639-1 code.
        """
        return self._payload["lang"]

    @property
    def country(self) -> str:
        """Country location of speaker.

        As ISO 3166-1 code.
        """
        return self._payload["country"]


class SpeakerLeft(Event):
    """Event emitted by the associated speaker when they left the conversation."""

    @property
    def timestamp(self) -> int:
        """UNIX time when the speaker left the conversation."""
        return self._payload["timestamp"]


class EntityFound(TimeScopedEvent):
    """The class for all entity annotation events."""

    def __init__(self, join_ref, ref, topic, event, payload):
        self._name = ENTITY_NAME.match(event).group(
            1
        )  # let it raise if it doesn't match
        super().__init__(join_ref, ref, topic, event, payload)

    @property
    def entity_name(self) -> str:
        """The name of the named entity found."""
        return self._name

    @property
    def lang(self) -> str:
        """Natural Language of the interpretation.

        As ISO 639-1 code.
        """
        return self._payload["lang"]

    @property
    def country(self) -> str:
        """Country location of speaker.

        As ISO 3166-1 code.
        """
        return self._payload["country"]

    @property
    def canonical(self) -> str:
        """The well formatted form of the entity in the language (string)."""
        return self._payload["annotation"].get("canonical")

    @property
    def original(self) -> str:
        """The transcript excerpt that was interpreted, as string."""
        return self._payload["annotation"]["original"]

    @property
    def value(self) -> Any:
        """The interpreted value in machine understandable form.

        The exact type depends on the entity.
        """
        return self._payload["annotation"].get("value")

    @property
    def confidence(self) -> float:
        """The confidence of the interpretation."""
        return self._payload["confidence"]

    def __repr__(self) -> str:
        return " ".join(
            (
                " - ",
                f"{self.__class__.__name__} in {self.speaker}:  <{self._name}> {self.canonical or self.original}",
                f"({self.value})" if self.value != self.canonical else "",
                f"[confidence: {self.confidence:.2f}]",
            )
        )


class Tag:
    """A tag represents a behavioral feature found in the conversation."""

    uuid: str
    """The unique id of the Tag."""
    label: str
    """The human readable name of the Tag."""

    def __init__(self, uuid: str, label: str) -> None:
        self.uuid = uuid
        self.label = label

    def __repr__(self) -> str:
        return f"Tag({self.label})"


class TagsFound(TimeScopedEvent):
    """One or more tags were found on this time range."""

    @property
    def lang(self) -> str:
        """Natural Language of the interpretation.

        As ISO 639-1 code.
        """
        return self._payload["lang"]

    @property
    def country(self) -> str:
        """Country location of speaker.

        As ISO 3166-1 code.
        """
        return self._payload["country"]

    @property
    def confidence(self) -> float:
        """Tagger confidence."""
        return self._payload["confidence"]

    @property
    def tags(self) -> List[Tag]:
        """The [tags][uhlive.stream.conversation.Tag] that were found on this time range"""
        return [Tag(t["uuid"], t["label"]) for t in self._payload["annotation"]["tags"]]

    def __repr__(self):
        return f"{self.__class__.__name__} in {self.speaker}:  {self.tags}"


class EntityReference:
    """Reference to a unique previously found Entity in the conversation."""

    kind: str
    """The name of the `Entity` referenced."""
    speaker: str
    """The speaker identifier."""
    start: int
    """The UNIX start time of the referenced `Entity`."""

    def __init__(self, entity_name: str, speaker: str, start: int) -> None:
        self.kind = entity_name
        self.speaker = speaker
        self.start = start

    def __repr__(self) -> str:
        return f"Ref({self.kind} by {self.speaker} at {human_datetime(self.start)})"


class RelationFound(TimeScopedEvent):
    """The class for all Relation events.

    Relations express a semantic relationship between two or more entities.
    """

    def __init__(self, join_ref, ref, topic, event, payload):
        self._name = RELATION_NAME.match(event).group(
            1
        )  # let it raise if it doesn't match
        super().__init__(join_ref, ref, topic, event, payload)

    @property
    def relation_name(self) -> str:
        """The type of the relation."""
        return self._name

    @property
    def lang(self) -> str:
        """Natural Language of the interpretation.

        As ISO 639-1 code.
        """
        return self._payload["lang"]

    @property
    def confidence(self) -> float:
        """The confidence on the discovered relationship."""
        return self._payload["confidence"]

    @property
    def members(self) -> List[EntityReference]:
        """[References to the Entities][uhlive.stream.conversation.EntityReference] involved in this relationship."""
        m = []
        speaker = self.speaker
        print(self._payload)
        for ref in self._payload["members"]:
            kind = (
                ENTITY_NAME.match(ref["entity"]).group(1) if ref["entity"] else None  # type: ignore
            )
            if kind is not None:
                m.append(EntityReference(kind, speaker, ref["start"]))
        return m

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} <{self._name}> for {self.members} [confidence: {self.confidence:.2f}]"


EVENT_MAP = {
    "words_decoded": WordsDecoded,
    "segment_decoded": SegmentDecoded,
    "segment_normalized": SegmentNormalized,
    "tags_found": TagsFound,
    "speaker_joined": SpeakerJoined,
    "speaker_left": SpeakerLeft,
    "phx_reply": Ok,
    "phx_close": Ok,
}
