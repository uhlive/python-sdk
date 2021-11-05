"""Samosa Events.

Data model for events returned by the Samosa server.
"""


import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class CompletionCause(Enum):
    """The set of possible completion cause"""

    GramDefinitionFailure = "GramDefinitionFailure"
    GramLoadFailure = "GramLoadFailure"
    Error = "Error"
    LanguageUnsupported = "LanguageUnsupported"
    NoInputTimeout = "NoInputTimeout"
    HotwordMaxtime = "HotwordMaxtime"
    NoMatch = "NoMatch"
    NoMatchMaxtime = "NoMatchMaxtime"
    TooMuchSpeechTimeout = "TooMuchSpeechTimeout"
    PartialMatchMaxtime = "PartialMatchMaxtime"
    Success = "Success"
    PartialMatch = "PartialMatch"


class Transcript:
    """The Transcript part of a recognition result"""

    def __init__(self, data: Dict[str, Any]) -> None:
        self._transcript: str = data["transcript"]
        self._confidence: float = float(data["confidence"])
        self._start = datetime.utcfromtimestamp(data["start"] / 1000.0)
        self._end = datetime.utcfromtimestamp(data["end"] / 1000.0)

    @property
    def transcript(self) -> str:
        return self._transcript

    @property
    def confidence(self) -> float:
        return self._confidence

    @property
    def start(self) -> datetime:
        return self._start

    @property
    def end(self) -> datetime:
        return self._end

    def __str__(self) -> str:
        return f'"{self._transcript}" ({self._confidence})'


class Interpretation:
    """The interpretation part of a recognition result"""

    def __init__(self, data: Dict[str, Any]) -> None:
        self._type: str = data["type"]
        self._value: Dict[str, Any] = data["value"]
        self._confidence: float = float(data["confidence"])

    @property
    def confidence(self) -> float:
        return self._confidence

    @property
    def type(self) -> str:
        """The type of the Interpretation is given by the builtin grammar URI"""
        return self._type

    @property
    def value(self) -> Dict[str, Any]:
        """The structured interpreted value.
        The type/schema of the value is given by the `type` attribute
        """
        return self._value

    def __str__(self) -> str:
        return f"[{self._type}] {self._value} ({self._confidence})"


class RecogResult:
    """When a recognition completes, this describe the result"""

    def __init__(self, data: dict) -> None:
        self._asr: Optional[Transcript] = (
            None if not data["asr"] else Transcript(data["asr"])
        )
        self._nlu: Optional[Interpretation] = (
            None if not data["nlu"] else Interpretation(data["nlu"])
        )
        self._grammar_uri: str = data["grammar_uri"]

    @property
    def asr(self) -> Optional[Transcript]:
        """The ASR part of the result (transcription result)"""
        return self._asr

    @property
    def nlu(self) -> Optional[Interpretation]:
        """The NLU part of the result (interpretation)"""
        return self._nlu

    @property
    def grammar_uri(self) -> str:
        """The grammar that matched, as it was given to the `RECOGNIZE` command"""
        return self._grammar_uri

    def __str__(self) -> str:
        return f"Transcript: {self._asr}\n ASR: {self._nlu}"


class Event:
    """Base class of all the events"""

    def __init__(self, data: Dict[str, Any]) -> None:
        self._request_id: int = int(data["request_id"])
        self._channel_id: str = data["channel_id"]
        self._headers: Dict[str, Any] = data["headers"]
        self._completion_cause: Optional[CompletionCause] = (
            None
            if not data["completion_cause"]
            else CompletionCause(data["completion_cause"])
        )
        self._completion_reason: Optional[str] = data["completion_reason"] or None
        self._body: Optional[RecogResult] = (
            None if not data["body"] else RecogResult(data["body"])
        )

    @property
    def request_id(self) -> int:
        return self._request_id

    @property
    def channel_id(self) -> str:
        return self._channel_id

    @property
    def headers(self) -> Dict[str, Any]:
        return self._headers

    @property
    def completion_cause(self) -> Optional[CompletionCause]:
        return self._completion_cause

    @property
    def completion_reason(self) -> Optional[str]:
        return self._completion_reason

    @property
    def body(self) -> Optional[RecogResult]:
        return self._body

    def __str__(self) -> str:
        return f"<Event {self.__class__.__name__}: {self._completion_cause} – {self._completion_reason} – {self._headers} – {self._body}"


class Opened(Event):
    pass


class ParamsSet(Event):
    pass


class DefaultParams(Event):
    """All the parameters and their values are in the `headers` property"""

    pass


class GrammarDefined(Event):
    pass


class RecognitionInProgress(Event):
    pass


class InputTimersStarted(Event):
    pass


class Stopped(Event):
    pass


class Closed(Event):
    pass


class StartOfInput(Event):
    pass


class RecognitionComplete(Event):
    pass


class MethodNotValid(Event):
    pass


class MethodFailed(Event):
    pass


class InvalidParamValue(Event):
    pass


class MissingParam(Event):
    pass


class MethodNotAllowed(Event):
    pass


EVENT_MAP = {
    "OPENED": Opened,
    "PARAMS-SET": ParamsSet,
    "DEFAULT-PARAMS": DefaultParams,
    "GRAMMAR-DEFINED": GrammarDefined,
    "RECOGNITION-IN-PROGRESS": RecognitionInProgress,
    "INPUT-TIMERS-STARTED": InputTimersStarted,
    "STOPPED": Stopped,
    "CLOSED": Closed,
    "START-OF-INPUT": StartOfInput,
    "RECOGNITION-COMPLETE": RecognitionComplete,
    "METHOD-NOT-VALID": MethodNotValid,
    "METHOD-FAILED": MethodFailed,
    "INVALID-PARAM-VALUE": InvalidParamValue,
    "MISSING-PARAM": MissingParam,
    "METHOD-NOT-ALLOWED": MethodNotAllowed,
}


def deserialize(data: str) -> Event:
    jd = json.loads(data)
    kind = jd["event"]
    if kind in EVENT_MAP:
        return EVENT_MAP[kind](jd)
    raise ValueError(f"Unknown event '{kind}'")


__all__ = [
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
