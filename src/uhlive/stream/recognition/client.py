"""
I/O free Connection state machine.
"""
import json
from typing import Any, Callable, Dict, Type, TypeVar

from .events import (
    Closed,
    Event,
    Opened,
    RecognitionComplete,
    RecognitionInProgress,
    Stopped,
    deserialize,
)


def serialize(cmd: Dict[str, Any]) -> str:
    return json.dumps(cmd, ensure_ascii=False, indent=None, separators=(",", ":"))


class ProtocolError(RuntimeError):
    pass


class State:
    """Protocol state.

    Protocol states implement and document the available commands.
    User code should not use the State directly but use a `Recognizer`
    object instead, and call the prococol methods on it.
    """

    def __init__(self, context: "Recognizer") -> None:
        self.context = context

    def command(self, name: str, headers: Dict[str, Any] = {}, body: str = "") -> str:
        return serialize(
            {
                "command": name,
                "request_id": self.context.request_id,
                "channel_id": self.context.channel_id,
                "headers": headers,
                "body": body,
            }
        )


class NoSessionState(State):
    def open(
        self, custom_id: str = "", channel_id: str = "", codec: str = "linear"
    ) -> str:
        """Open a new Samosa session.

        ``custom_id`` is any reference of yours that you want to appear in the logs
        and invoice reports.

        If a ``channel_id`` is provided, it'll be used as a prefix for
        the actual channel ID generated by the server.

        ``codec`` is the speech audio codec of the audio data:
            - ``"linear"``: (default) linear 16 bit SLE raw PCM audio at 8khz;
            - ``"g711a"``: G711 a-law audio at 8khz;
            - ``"g711u"``: G711 μ-law audio at 8khz.

        """
        return serialize(
            {
                "command": "OPEN",
                "request_id": self.context.request_id,
                "channel_id": channel_id,
                "headers": {"custom_id": custom_id, "audio_codec": codec},
                "body": "",
            }
        )


class IdleSessionState(State):
    def send_audio_chunk(self, chunk: bytes) -> bytes:
        """Build an audio chunk frame for streaming."""
        return chunk

    def set_params(self, **params: Any) -> str:
        """Set default ASR parameters for the session.

        See https://docs.allo-media.net/live-api/robots-humans-protocol/#set-session-defaults
        for an explanation of the different parameters available.
        """

        return self.command("SET-PARAMS", params)

    def get_params(self) -> str:
        """Retrieve the default values for the ASR parameters."""
        return self.command("GET-PARAMS")

    def define_grammar(self, builtin: str, alias: str) -> str:
        """Define a grammar alias for a parameterized builtin.

        `builtin`: the builtin URI to alias, including the query string, but without the "builtin:" prefix
        `alias`: the alias, without the "session:" prefix.
        """
        return self.command(
            "DEFINE-GRAMMAR",
            {"content_id": alias, "content_type": "text/uri-list"},
            f"builtin:{builtin}",
        )

    def recognize(
        self,
        *grammars: str,
        start_timers: bool = True,
        recognition_mode: str = "normal",
        **params: Any,
    ) -> str:
        """Start a recognition process.

        This method takes grammar URIs as positional arguments, including the `builtin:` or
        `session:` prefixes to make the difference between builtin grammars and custom aliases.

        Keywords arguments are also accepted:
          - `start_timers`: default True
          - `recognition_mode`: default is "normal"
          - any other ASR parameter (no client side defaults).

        See https://docs.allo-media.net/live-api/robots-humans-protocol/#start-recognition
        """
        return self.command(
            "RECOGNIZE",
            headers={
                "recognition_mode": recognition_mode,
                "content_type": "text/uri-list",
                "start_input_timers": start_timers,
                **params,
            },
            body="\n".join(grammars),
        )

    def close(self) -> str:
        """Close the current session."""
        return self.command("CLOSE")


class RecognitionState(State):
    def send_audio_chunk(self, chunk: bytes) -> bytes:
        """Build an audio chunk frame for streaming."""
        return chunk

    def start_input_timers(self) -> str:
        """If the input timers were not started by the RECOGNIZE command,
        starts them now.
        """
        return self.command("START-INPUT-TIMERS")

    def stop(self) -> str:
        """Stop ongoing recognition process"""
        return self.command("STOP")


S = TypeVar("S", bound=State)


class Recognizer:
    """The connection state machine.

    Use this class to decode received frames as `Event`s or to
    make command frames by calling the appropriate methods.
    If you call a method that is not appropriate in the current protocol
    state, a `ProtocolError` is raised.
    """

    def __init__(self) -> None:
        self._state: State = NoSessionState(self)
        self._request_id = 0
        self._channel_id = ""

    def __getattr__(self, name: str) -> Callable:
        meth = getattr(self._state, name, None)
        if meth is None:
            raise ProtocolError(f"no method '{name}' in this state!")
        return meth

    def transition(self, state: Type[S]) -> None:
        self._state = state(self)

    @property
    def request_id(self) -> int:
        self._request_id += 1
        return self._request_id

    @property
    def channel_id(self) -> str:
        return self._channel_id

    def receive(self, data: str) -> Event:
        """Decode received text frame"""
        event = deserialize(data)
        if isinstance(event, RecognitionInProgress):
            self.transition(RecognitionState)
        elif isinstance(event, (RecognitionComplete, Stopped)):
            self.transition(IdleSessionState)
        elif isinstance(event, Opened):
            self._channel_id = event.channel_id
            self.transition(IdleSessionState)
        elif isinstance(event, Closed):
            self.transition(NoSessionState)
        return event
