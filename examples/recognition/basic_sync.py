import os
import time
from queue import Empty, Queue
from threading import Thread

import websocket as ws  # type: ignore

from uhlive.stream.recognition import Closed
from uhlive.stream.recognition import CompletionCause as CC
from uhlive.stream.recognition import (
    GrammarDefined,
    Opened,
    ParamsSet,
    RecognitionComplete,
    RecognitionInProgress,
    Recognizer,
    StartOfInput,
)


def init_bytes(size, value):
    return bytes([value]) * size


CODEC_HINTS = {"linear": (960, 0), "g711a": (480, 0x55), "g711u": (480, 0xFF)}


class AudioStreamer(Thread):
    def __init__(self, socket, client, verbose=True):
        Thread.__init__(self)
        self.socket = socket
        self.client = client
        self.verbose = verbose
        self.fileq = Queue(5)
        self._should_stop = False
        self._should_skip = False
        self._chunk_size = 960
        self._silence = init_bytes(self._chunk_size, 0)

    def stop(self):
        self._should_stop = True

    def skip(self):
        self._should_skip = True

    def run(self):
        while not self._should_stop:
            # stream silence when idle
            self.socket.send_binary(self.client.send_audio_chunk(self._silence))
            try:
                audio = self.fileq.get(timeout=0.06)
            except Empty:
                continue
            self._should_skip = False
            if self.verbose:
                print(f"Streaming file in realtime: {audio} for transcription!")
            with open(audio, "rb") as audio_file:
                while not self._should_skip:
                    audio_chunk = audio_file.read(self._chunk_size)
                    if not audio_chunk:
                        break
                    self.socket.send_binary(self.client.send_audio_chunk(audio_chunk))
                    time.sleep(0.06)
            if self.verbose:
                print(f"File {audio} successfully streamed")

    def play(self, filename, codec="linear"):
        self._chunk_size, silence_value = CODEC_HINTS[codec]
        self._silence = init_bytes(self._chunk_size, silence_value)
        self.fileq.put_nowait(filename)


def main(socket: ws.WebSocket, client: Recognizer, stream: AudioStreamer):

    # Shortcuts
    send = socket.send

    def expect(*event_classes):
        event = client.receive(socket.recv())
        assert isinstance(event, event_classes), f"expected {event_classes} got {event}"
        return event

    # scenario

    send(client.open("mytest"))
    expect(Opened)
    stream.start()

    send(client.set_params(speech_language="fr", no_input_timeout=5000))
    expect(ParamsSet)

    # Recognize address
    stream.play("fixtures/fr_address_ok.pcm")
    send(
        client.recognize(
            "builtin:speech/postal_address",
            speech_complete_timeout=800,
            no_input_timeout=5000,
        )
    )
    expect(RecognitionInProgress)

    expect(StartOfInput)
    event = expect(RecognitionComplete)
    cc = event.completion_cause
    result = event.body
    if cc == CC.Success:
        print("Got complete address:", result.nlu.value)
    elif cc == CC.PartialMatch:
        print("Got partial address:", result.nlu.value)
    else:
        print(cc)
        if result.asr:
            print("Unable to find an address in", result.asr.transcript)
        else:
            print("No transcript")

    stream.skip()
    # Recognize parcel number
    send(
        client.define_grammar(
            "speech/spelling/mixed?regex=[a-z]{2}[0-9]{9}[a-z]{2}", "parcel"
        )
    )
    expect(GrammarDefined)

    stream.play("fixtures/parcel_number.pcm")
    send(
        client.recognize(
            "session:parcel",
            hotword_max_duration=10000,
            no_input_timeout=5000,
            recognition_mode="hotword",
        )
    )
    expect(RecognitionInProgress)

    event = expect(RecognitionComplete)
    cc = event.completion_cause
    result = event.body
    if cc == CC.Success:
        print("Got well formed parcel number:", result.nlu.value)
    else:
        print(cc)
        if result.asr:
            print("Unable to find a parcel number in", result.asr.transcript)
        else:
            print("No transcript")

    stream.skip()
    stream.stop()
    send(client.close())
    expect(Closed)


if __name__ == "__main__":
    uhlive_url = os.environ["UHLIVE_API_URL"]
    uhlive_token = os.environ["UHLIVE_API_TOKEN"]
    socket = ws.create_connection(
        uhlive_url, header={"Authorization": f"bearer {uhlive_token}"}
    )
    client = Recognizer()
    stream = AudioStreamer(socket, client)
    try:
        main(socket, client, stream)
    finally:
        stream.stop()
        stream.join()
        socket.close()
