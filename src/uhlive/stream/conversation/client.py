"""
Object oriented abstraction over the Conversation API protocol and workflow.
"""

import json
from array import array
from enum import Enum
from typing import Any, Dict, Union

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
    """Exception raised when a [Conversation][uhlive.stream.conversation.Conversation] method is not available in the current state."""

    pass


class State(Enum):
    """Protocol state."""

    Idle = "Idle State"
    Joined = "Joined State"


class Conversation:
    """To join a conversation on the API, you need a `Conversation` object.

    You can only have one `Conversation` per connection (socket) otherwise you risk
    unexpected behavior (and exceptions!).
    """

    def __init__(self, identifier: str, conversation_id: str, speaker: str) -> None:
        """Create a `Conversation`.

        Args:
            identifier: is the identifier you got when you subscribed to the service;
            conversation_id: is the conversation you wish to join,
            speaker: is your alias in the conversation, to identify you and your events
        """
        self._state: State = State.Idle
        self.identifier = identifier
        self.topic = f"conversation:{self.identifier}@{conversation_id}"
        self.topic_bin = self.topic.encode("utf-8")
        self.topic_len = len(self.topic_bin)
        self.speaker = speaker
        self._request_id = int(S_JOIN_REF) - 1

    def join(
        self,
        model: str = "fr",
        country: str = "fr",
        readonly: bool = False,
        interim_results: bool = True,
        rescoring: bool = True,
        origin: int = 0,
        audio_codec: str = "linear",
    ) -> str:
        """Join the conversation.

        Args:
            readonly: if you are not going to stream audio, set it to `True`.
            model: (if `readonly` is `False`) the ASR language model to be use to recognize
                     the audio you will stream.
            country: the iso 2 letter country code of the place where the speaker is.
            interim_results: (`readonly` = `False` only) should the ASR trigger interim result events?
            rescoring: (`readonly` = `False` only) should the ASR refine the final segment
                         with a bigger Language Model?
                         May give slightly degraded results for very short segments.
            origin: The UNIX time, in milliseconds, to which the event timeline origin is set.
            audio_codec: the speech audio codec of the audio data:

                - `"linear"`: (default) linear 16 bit SLE raw PCM audio at 8khz;
                - `"g711a"`: G711 a-law audio at 8khz;
                - `"g711u"`: G711 μ-law audio at 8khz.

        Returns:
            The text websocket message to send to the server.

        Raises:
            ProtocolError: if still in a previously joined conversation.
        """
        if self._state != State.Idle:
            raise ProtocolError("Can't join twice!")
        if not readonly and not model:
            raise ProtocolError("If readonly is False, you must specify a model!")
        return self.command(
            "phx_join",
            {
                "readonly": readonly,
                "speaker": self.speaker,
                "model": model,
                "country": country,
                "interim_results": interim_results,
                "rescoring": rescoring,
                "origin": origin,
                "audio_codec": audio_codec,
            },
        )

    def leave(self) -> str:
        """Leave the current conversation.

        It's a good idea to leave a conversation and continue to consume messages
        until you receive a [`SpeakerLeft`][uhlive.stream.conversation.SpeakerLeft] event for your speaker, before you
        close the connection. Otherwise, you may miss parts of the transcription.

        Returns:
            The text websocket message to send to the server.

        Raises:
            ProtocolError: if not currently in a converstation.
        """
        if self._state != State.Joined:
            raise ProtocolError("No conversation to leave!")
        return self.command("phx_leave", {})

    def send_audio_chunk(self, chunk: bytes) -> bytes:
        """Build an audio chunk for streaming.

        Returns:
            The binary websocket message to send to the server.
        Raises:
            ProtocolError: if not currently in a converstation.
        """
        if self._state != State.Joined:
            raise ProtocolError("Not in a conversation!")
        ref = self.request_id.encode("ascii")
        message = array("B", [0, 1, len(ref), self.topic_len, 11, B_JOIN_REF])
        message.extend(ref)
        message.extend(self.topic_bin)
        message.extend(b"audio_chunk")
        message.extend(chunk)
        return message.tobytes()

    @property
    def request_id(self) -> str:
        self._request_id += 1
        return str(self._request_id)

    def receive(self, data: Union[str, bytes]) -> Event:
        """Decode received websocket message.

        The server only sends text messages.

        Returns:
            The appropriate [Event][uhlive.stream.conversation.Event] subclass instance.
        """
        event = Event.from_message(json.loads(data))
        assert (
            event.topic == self.topic
        ), "Topic mismatch! Are you trying to mix several conversations on the same socket? This is not supported."
        if isinstance(event, Ok) and event.ref == event.join_ref:
            self._state = State.Joined
        elif isinstance(event, SpeakerLeft) and event.speaker == self.speaker:
            self._state = State.Idle
        return event

    @property
    def left(self):
        """Did the server confirm we left the conversation?"""
        return self._state == State.Idle

    def command(self, name: str, payload: Dict[str, Any] = {}) -> str:
        message = [
            S_JOIN_REF,
            self.request_id,
            self.topic,
            name,
            payload,
        ]
        return json.dumps(
            message, ensure_ascii=False, indent=None, separators=(",", ":")
        )
