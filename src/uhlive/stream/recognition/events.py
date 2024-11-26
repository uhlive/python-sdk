"""H2B Events.

Data model for events returned by the H2B server.
See also https://docs.allo-media.net/stream-h2b/protocols/websocket/#websocket-for-voicebots.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class CompletionCause(Enum):
    """The set of possible completion causes.

    See [all possible values](https://docs.allo-media.net/stream-h2b/protocols/websocket/#asynchronous-recognition-events).
    """

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
        """The raw ASR output."""
        return self._transcript

    @property
    def confidence(self) -> float:
        """The ASR transcription confidence."""
        return self._confidence

    @property
    def start(self) -> datetime:
        """Start of speech."""
        return self._start

    @property
    def end(self) -> datetime:
        """End of speech."""
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
        """The confidence of the interpretation."""
        return self._confidence

    @property
    def type(self) -> str:
        """The type of the Interpretation is given by the builtin grammar URI"""
        return self._type

    @property
    def value(self) -> Dict[str, Any]:
        """The structured interpreted value.

        The type/schema of the value is given by the `self.type` property.

        See the [Grammar reference documentaiton](https://docs.allo-media.net/stream-h2b/grammars).
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
        if "alternatives" in data:
            self._alternatives = [RecogResult(alt) for alt in data["alternatives"]]

    @property
    def asr(self) -> Optional[Transcript]:
        """The ASR part of the result ([transcription][uhlive.stream.recognition.Transcript] result)"""
        return self._asr

    @property
    def nlu(self) -> Optional[Interpretation]:
        """The NLU part of the result ([interpretation][uhlive.stream.recognition.Interpretation])"""
        return self._nlu

    @property
    def grammar_uri(self) -> str:
        """The grammar that matched, as it was given to the `RECOGNIZE` command"""
        return self._grammar_uri

    @property
    def alternatives(self) -> List["RecogResult"]:
        """if N-bests were requested, the additional results besides the best one are there."""
        return getattr(self, "_alternatives", [])

    def __str__(self) -> str:
        best = f"Transcript: {self._asr}\n NLU: {self._nlu}"
        if hasattr(self, "_alternatives"):
            alt_str = "\n   ".join(str(alt) for alt in self._alternatives)
            return f"{best}\nAlternatives:\n   {alt_str}"
        else:
            return best


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
        """The request ID that event responds to."""
        return self._request_id

    @property
    def channel_id(self) -> str:
        """The channel ID."""
        return self._channel_id

    @property
    def headers(self) -> Dict[str, Any]:
        """The response headers.

        See also the [header description](https://docs.allo-media.net/stream-h2b/output/#headers-%26-statuses).
        """
        return self._headers

    @property
    def completion_cause(self) -> Optional[CompletionCause]:
        """The response [`CompletionCause`][uhlive.stream.recognition.CompletionCause]."""
        return self._completion_cause

    @property
    def completion_reason(self) -> Optional[str]:
        """The completion message."""
        return self._completion_reason

    @property
    def body(self) -> Optional[RecogResult]:
        """The content of the Event is a [`RecogResult`][uhlive.stream.recognition.RecogResult] if it is a `RecognitionComplete` event."""
        return self._body

    def __str__(self) -> str:
        return f"<Event {self.__class__.__name__}: {self._completion_cause} – {self._completion_reason} – {self._headers} – {self._body}"


class Opened(Event):
    """Session opened on the server"""

    pass


class ParamsSet(Event):
    """The default parameters were set."""

    pass


class DefaultParams(Event):
    """All the parameters and their values are in the `headers` property"""

    pass


class GrammarDefined(Event):
    """The `DefineGrammar` command has been processed."""

    pass


class RecognitionInProgress(Event):
    """The ASR recognition is started."""

    pass


class InputTimersStarted(Event):
    """The Input Timers are started."""

    pass


class Stopped(Event):
    """The ASR recognition has been stopped on the client request."""

    pass


class Closed(Event):
    """The session is closed."""

    pass


class StartOfInput(Event):
    """In normal recognition mode, this event is emitted when speech is detected."""

    pass


class RecognitionComplete(Event):
    """The ASR recognition is complete."""

    pass


class MethodNotValid(Event):
    """The server received an invalid command."""

    pass


class MethodFailed(Event):
    """The server was unable to complete the command."""

    pass


class InvalidParamValue(Event):
    """The server received a request to set an invalid value for a parameter."""

    pass


class MissingParam(Event):
    """The command is missings some mandatory parameter."""

    pass


class MethodNotAllowed(Event):
    """The command is not allowed in this state."""

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
