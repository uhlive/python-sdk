"""Event definitions."""

import re
from typing import List

from .error import UhliveError
from .human_datetime import human_datetime

ENTITY_NAME = re.compile(r"entity_([\w_]+)_found")
RELATION_NAME = re.compile(r"relation_([\w_]+)_found")


class Word(dict):
    """Timestamped word."""

    @property
    def start(self):
        """Start time as Unix timestamp in millisecond, according to audio timeline."""
        return self["start"]

    @property
    def end(self):
        """End time as Unix timestamp in millisecond, according to audio timeline."""
        return self["end"]

    @property
    def length(self):
        """Word length in millisecond, according to audio timeline."""
        return self["length"]

    @property
    def word(self):
        """Transcript token string for this word."""
        return self["word"]

    @property
    def confidence(self):
        return self["confidence"]


class Event(object):
    """The base class of all events."""

    def __init__(self, join_ref, ref, topic, event, payload) -> None:
        self._join_ref = join_ref
        self._ref = ref
        self._topic = topic
        self._payload = payload

    def __repr__(self):
        return f"{self.__class__.__name__}(payload={self._payload})"

    @property
    def join_ref(self):
        return self._join_ref

    @property
    def ref(self):
        return self._ref

    @property
    def speaker(self):
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
    pass


class Unknown(Event):
    def __init__(self, join_ref, ref, topic, event, payload):
        self._name = event
        super().__init__(join_ref, ref, topic, event, payload)

    def __repr__(self):
        return f"Unknown [{self._name}](payload={self._payload})"


class TimeScopedEvent(Event):
    """Base class for events that are anchored to the audio time line."""

    @property
    def start(self):
        """Start time as Unix timestamp in millisecond, according to audio timeline."""
        return self._payload["start"]

    @property
    def end(self):
        """End time as Unix timestamp in millisecond, according to audio timeline."""
        return self._payload["end"]

    @property
    def length(self):
        """Event length in millisecond, according to audio timeline."""
        return self._payload["length"]


class SpeechDecoded(TimeScopedEvent):
    """The base class of all transcription events."""

    @property
    def transcript(self):
        """Get the transcript of the whole segment as a string"""
        return self._payload["transcript"]

    @property
    def lang(self):
        """Natural Language of the speech.

        As ISO 639-1 code.
        """
        return self._payload["lang"]

    @property
    def country(self):
        """Country location of speaker.

        As ISO 3166-1 code.
        """
        return self._payload["country"]

    @property
    def utterance_id(self):
        """The Utterance id identifies the speech utterance this event transcribes."""
        return self._payload["utterance_id"]

    @property
    def words(self):
        """Get the transcript of the whole segment as a list of timestamped words."""
        return [Word(w) for w in self._payload["words"]]

    def __str__(self):
        return f"[{self.speaker} — {human_datetime(self.start)}] {self.transcript}"


class WordsDecoded(SpeechDecoded):
    """Interim segment transcript event."""

    pass


class SegmentDecoded(SpeechDecoded):
    """Final segment transcript event."""

    pass


class SpeakerJoined(Event):
    @property
    def timestamp(self):
        return self._payload["timestamp"]

    @property
    def interim_results(self):
        return self._payload["interim_results"]

    @property
    def rescoring(self):
        return self._payload["rescoring"]

    @property
    def lang(self):
        """Natural Language of the speech.

        As ISO 639-1 code.
        """
        return self._payload["lang"]

    @property
    def country(self):
        """Country location of speaker.

        As ISO 3166-1 code.
        """
        return self._payload["country"]


class SpeakerLeft(Event):
    """Event emitted by the associated speaker when they left the conversation."""

    @property
    def timestamp(self):
        return self._payload["timestamp"]


class EntityFound(TimeScopedEvent):
    """The class for all entity annotation events."""

    def __init__(self, join_ref, ref, topic, event, payload):
        self._name = ENTITY_NAME.match(event).group(
            1
        )  # let it raise if it doesn't match
        super().__init__(join_ref, ref, topic, event, payload)

    @property
    def entity_name(self):
        return self._name

    @property
    def lang(self):
        """Natural Language of the interpretation.

        As ISO 639-1 code.
        """
        return self._payload["lang"]

    @property
    def country(self):
        """Country location of speaker.

        As ISO 3166-1 code.
        """
        return self._payload["country"]

    @property
    def canonical(self):
        """The well formatted form of the entity in the language (string)."""
        return self._payload["annotation"].get("canonical")

    @property
    def original(self):
        """The transcript excerpt that was interpreted, as string."""
        return self._payload["annotation"]["original"]

    @property
    def value(self):
        """The interpreted value in machine understandable form.

        The exact type depends on the entity.
        """
        return self._payload["annotation"].get("value")

    @property
    def confidence(self):
        return self._payload["confidence"]

    def __repr__(self):
        return " ".join(
            (
                f"{self.__class__.__name__} in {self.speaker}:  <{self._name}> {self.canonical or self.original}",
                f"({self.value})" if self.value != self.canonical else "",
                f"[confidence: {self.confidence:.2f}]",
            )
        )


class Tag:
    uuid: str
    label: str

    def __init__(self, uuid: str, label: str) -> None:
        self.uuid = uuid
        self.label = label

    def __repr__(self) -> str:
        return f"Tag({self.label})"


class TagsFound(TimeScopedEvent):
    @property
    def lang(self):
        """Natural Language of the interpretation.

        As ISO 639-1 code.
        """
        return self._payload["lang"]

    @property
    def country(self):
        """Country location of speaker.

        As ISO 3166-1 code.
        """
        return self._payload["country"]

    @property
    def confidence(self):
        return self._payload["confidence"]

    @property
    def tags(self) -> List[Tag]:
        return [Tag(t["uuid"], t["label"]) for t in self._payload["annotation"]["tags"]]

    def __repr__(self):
        return f"{self.__class__.__name__} in {self.speaker}:  {self.tags}"


class EntityReference:
    """Reference to unique Entity in conversation."""

    kind: str
    speaker: str
    start: int

    def __init__(self, entity_name: str, speaker: str, start: int) -> None:
        self.kind = entity_name
        self.speaker = speaker
        self.start = start

    def __repr__(self) -> str:
        return f"Ref({self.kind} by {self.speaker} at {human_datetime(self.start)})"


class RelationFound(TimeScopedEvent):
    """The class for all Relation events."""

    def __init__(self, join_ref, ref, topic, event, payload):
        self._name = RELATION_NAME.match(event).group(
            1
        )  # let it raise if it doesn't match
        super().__init__(join_ref, ref, topic, event, payload)

    @property
    def relation_name(self):
        return self._name

    @property
    def lang(self):
        """Natural Language of the interpretation.

        As ISO 639-1 code.
        """
        return self._payload["lang"]

    @property
    def confidence(self):
        return self._payload["confidence"]

    @property
    def members(self):
        m = []
        speaker = self.speaker
        print(self._payload)
        for ref in self._payload["members"]:
            kind = ENTITY_NAME.match(ref["entity"]).group(1) if ref["entity"] else None
            if kind is not None:
                m.append(EntityReference(kind, speaker, ref["start"]))
        return m

    def __repr__(self):
        return f"{self.__class__.__name__} <{self._name}> for {self.members} [confidence: {self.confidence:.2f}]"


EVENT_MAP = {
    "words_decoded": WordsDecoded,
    "segment_decoded": SegmentDecoded,
    "tags_found": TagsFound,
    "speaker_joined": SpeakerJoined,
    "speaker_left": SpeakerLeft,
    "phx_reply": Ok,
    "phx_close": Ok,
}
