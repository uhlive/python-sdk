import json
from array import array
from typing import Any, Callable, Dict, Type, TypeVar

from .events import Event, Ok, SpeakerLeft

# *** Phoenix channel protocol V2 ***
#
# This is a non-official "specification" translated from Phoenix source code.
#
# Compared to the V1 protocol.
#
# * A new message field has been added: `join_ref`, which is the `ref` string when joining. We use "0".
# * JSON messages: instead of an object that names the fields, V2 sends a list
#   (i.e parameters are passed by position instead of being passed by name) in this order:
#      join_ref, ref, topic, event_name, payload
# * We now have a binary version represented as (using erlang binary patterns):
# <<
#  @push::size(8),
#  join_ref_size::size(8),
#  ref_size::size(8),
#  topic_size::size(8),
#  event_size::size(8),
#  join_ref::binary-size(join_ref_size),
#  ref::binary-size(ref_size),
#  topic::binary-size(topic_size),
#  event::binary-size(event_size),
#  data::binary
# >>
# where @push = 0

B_JOIN_REF = ord("1")
S_JOIN_REF = "1"


class ProtocolError(RuntimeError):
    pass


class State:
    """Protocol state.

    Protocol states implement and document the available commands.
    User code should not use the State directly but use a `Conversation`
    object instead, and call the prococol methods on it.
    """

    def __init__(self, context: "Conversation") -> None:
        self.context = context

    def command(self, name: str, payload: Dict[str, Any] = {}) -> str:
        message = [
            S_JOIN_REF,
            self.context.request_id,
            self.context.topic,
            name,
            payload,
        ]
        return json.dumps(
            message, ensure_ascii=False, indent=None, separators=(",", ":")
        )


class IdleState(State):
    def join(
        self,
        model="fr",
        country="fr",
        readonly: bool = False,
        interim_results=True,
        rescoring=True,
        origin=0,
        audio_codec="linear",
    ) -> str:
        """Join the conversation.

        * ``readonly``: if you are not going to stream audio, set it to ``True``.
        * ``speaker``: your alias in the conversation, to identify you and your events.
        * ``model``: (if ``readonly`` is ``False``) the ASR language model to be use to recognize
                     the audio you will stream.
        * ``country``: the iso 2 letter country code of the place where the speaker is.
        * ``interim_results``: (``readonly`` = ``False`` only) should the ASR trigger interim result events?
        * ``rescoring``: (``readonly`` = ``False`` only) should the ASR refine the final segment
                         with a bigger Language Model?
                         May give slightly degraded results for very short segments.
        * ``codec``: the speech audio codec of the audio data:
            - ``"linear"``: (default) linear 16 bit SLE raw PCM audio at 8khz;
            - ``"g711a"``: G711 a-law audio at 8khz;
            - ``"g711u"``: G711 μ-law audio at 8khz.
        """
        if not readonly and not model:
            raise ProtocolError("If readonly is False, you must specify a model!")
        return self.command(
            "phx_join",
            {
                "readonly": readonly,
                "speaker": self.context.speaker,
                "model": model,
                "country": country,
                "interim_results": interim_results,
                "rescoring": rescoring,
                "origin": origin,
                "audio_codec": audio_codec,
            },
        )


class JoinedState(State):
    def leave(self) -> str:
        """Leave the current conversation.

        It's a good idea to leave a conversation and continue to consume messages
        until you receive a SpeakerLeft event for your speaker, before you
        close the connection. Otherwise, you may miss parts of the transcription.
        """
        return self.command("phx_leave", {})

    def send_audio_chunk(self, chunk: bytes) -> bytes:
        """Send an audio chunk (when streaming.)."""
        ref = self.context.request_id.encode("ascii")
        message = array("B", [0, 1, len(ref), self.context.topic_len, 11, B_JOIN_REF])
        message.extend(ref)
        message.extend(self.context.topic_bin)
        message.extend(b"audio_chunk")
        message.extend(chunk)
        return message.tobytes()


S = TypeVar("S", bound=State)


class Conversation:
    """To join a conversation on the API, you need a `Conversation` object"""

    def __init__(self, identifier: str, conversation_id: str, speaker: str) -> None:
        """Create a `Conversation`.
        - `identifier` is the identifier you got when you subscribed to the service;
        - `conversation_id` is the conversation you wish to join,
        - `speaker` is your alias in the conversation, to identify you and your events
        """
        self._state: State = IdleState(self)
        self.identifier = identifier
        self.topic = f"conversation:{self.identifier}@{conversation_id}"
        self.topic_bin = self.topic.encode("utf-8")
        self.topic_len = len(self.topic_bin)
        self.speaker = speaker
        self._request_id = int(S_JOIN_REF) - 1

    def __getattr__(self, name: str) -> Callable:
        meth = getattr(self._state, name, None)
        if meth is None:
            raise ProtocolError(f"no method '{name}' in this state!")
        return meth

    def transition(self, state: Type[S]) -> None:
        self._state = state(self)

    @property
    def request_id(self) -> str:
        self._request_id += 1
        return str(self._request_id)

    def receive(self, data: str) -> Event:
        """Decode received text frame"""
        event = Event.from_message(json.loads(data))
        if isinstance(event, Ok) and event.ref == event.join_ref:
            self.transition(JoinedState)
        elif isinstance(event, SpeakerLeft) and event.speaker == self.speaker:
            self.transition(IdleState)
        return event

    @property
    def left(self):
        return isinstance(self._state, IdleState)
