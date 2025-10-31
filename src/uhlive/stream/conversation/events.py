"""Event definitions."""

import re
from typing import Any, List

from .error import UhliveError
from .human_datetime import human_datetime

ENTITY_NAME = re.compile(r"entity_([\w_]+)_recognized")
RELATION_NAME = re.compile(r"relation_([\w_]+)_recognized")


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
    def value(self) -> str:
        """Transcript token string for this word."""
        return self["value"]

    @property
    def confidence(self) -> float:
        """ASR confidence for this word."""
        return self["confidence"]


class Event(object):
    """The base class of all events."""

    def __init__(self, join_ref, ref, conversation, event, payload) -> None:
        self._join_ref = join_ref
        self._ref = ref
        self._conversation = conversation
        self._payload = payload

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(payload={self._payload})"

    @property
    def conversation(self) -> str:
        """The conversation identifier"""
        return self._conversation

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
            return EntityRecognized(*message)
        if event.startswith("relation_"):
            return RelationRecognized(*message)
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


class AudioSpeechDecoded(TimeScopedEvent):
    """The base class of all transcription events."""

    @property
    def value(self) -> str:
        """Get the transcript of the whole segment as a string"""
        return self._payload["value"]

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
    def id(self) -> str:
        """The Utterance id identifies the speech utterance this event transcribes."""
        return self._payload["id"]

    @property
    def components(self) -> List[Word]:
        """Get the transcript of the whole segment as a list of timestamped [words][uhlive.stream.conversation.Word]."""
        return [Word(w) for w in self._payload["components"]]

    def __str__(self) -> str:
        return f"[{self.speaker} — {human_datetime(self.start)}] {self.value}"

    @property
    def confidence(self) -> float:
        """The ASR confidence for this segment."""
        return self._payload["confidence"]


class AudioWordsDecoded(AudioSpeechDecoded):
    """Interim segment transcript event."""

    pass


class AudioSegmentDecoded(AudioSpeechDecoded):
    """Final segment transcript event."""

    pass


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


class EntityRecognized(TimeScopedEvent):
    """The class for all entity annotation events."""

    def __init__(self, join_ref, ref, conversation, event, payload):
        self._name = ENTITY_NAME.match(event).group(
            1
        )  # let it raise if it doesn't match
        super().__init__(join_ref, ref, conversation, event, payload)

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
    def display(self) -> str | None:
        """The well formatted form of the entity in the language (string)."""
        return self._payload.get("display")

    @property
    def source(self) -> str:
        """The transcript excerpt that was interpreted, as string."""
        return self._payload["source"]

    @property
    def value(self) -> Any:
        """The interpreted value in machine understandable form.

        The exact type depends on the entity.
        """
        return self._payload.get("value")

    @property
    def confidence(self) -> float:
        """The confidence of the interpretation."""
        return self._payload["confidence"]

    def __repr__(self) -> str:
        return " ".join(
            (
                " - ",
                f"{self.__class__.__name__} in {self.speaker}:  <{self._name}> {self.display or self.source}",
                f"({self.value})" if self.value != self.display else "",
                f"[confidence: {self.confidence:.2f}]",
            )
        )


class Tag:
    """A tag represents a behavioral feature found in the conversation."""

    value: str
    """The unique id of the Tag."""
    display: str
    """The human readable name of the Tag."""

    confidence: float

    def __init__(self, value: str, display: str, confidence: float) -> None:
        self.value = value
        self.display = display
        self.confidence = confidence

    def __repr__(self) -> str:
        return f"Tag({self.display})"


class TagsSet(TimeScopedEvent):
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
        return [
            Tag(t["value"], t["display"], t["confidence"])
            for t in self._payload["components"]
        ]

    def __repr__(self):
        return f"{self.__class__.__name__} in {self.speaker}:  {self.tags}"


class EntityReference:
    """Reference to a unique previously found Entity in the conversation."""

    kind: str
    """The name of the `Entity` referenced."""
    speaker: str
    """The speaker identifier."""
    id: str
    """The id the referenced `Entity`."""

    def __init__(self, entity_name: str, speaker: str, id: str) -> None:
        self.kind = entity_name
        self.speaker = speaker
        self.id = id

    def __repr__(self) -> str:
        return f"Ref({self.kind} by {self.speaker} with id {self.id}"


class RelationRecognized(TimeScopedEvent):
    """The class for all Relation events.

    Relations express a semantic relationship between two or more entities.
    """

    def __init__(self, join_ref, ref, conversation, event, payload):
        self._name = RELATION_NAME.match(event).group(
            1
        )  # let it raise if it doesn't match
        super().__init__(join_ref, ref, conversation, event, payload)

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
    def components(self) -> List[EntityReference]:
        """[References to the Entities][uhlive.stream.conversation.EntityReference] involved in this relationship."""
        m = []
        speaker = self.speaker
        print(self._payload)
        for ref in self._payload["components"]:
            kind = (
                ENTITY_NAME.match(ref["class"]).group(1) if ref["class"] else None  # type: ignore
            )
            if kind is not None:
                m.append(EntityReference(kind, speaker, ref["id"]))
        return m

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} <{self._name}> for {self.components} [confidence: {self.confidence:.2f}]"


EVENT_MAP = {
    "audio_words_decoded": AudioWordsDecoded,
    "audio_segment_decoded": AudioSegmentDecoded,
    "tags_set": TagsSet,
    "speaker_joined": SpeakerJoined,
    "speaker_left": SpeakerLeft,
    "phx_reply": Ok,
    "phx_close": Ok,
}
