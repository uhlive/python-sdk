import os

import requests
import websocket as ws  # type: ignore
from basic_sync import AudioStreamer

from uhlive.auth import build_authentication_request
from uhlive.stream.recognition import Closed
from uhlive.stream.recognition import CompletionCause as CC
from uhlive.stream.recognition import (
    Opened,
    ParamsSet,
    RecognitionComplete,
    RecognitionInProgress,
    Recognizer,
    StartOfInput,
    build_connection_request,
)


def main(
    socket: ws.WebSocket,
    client: Recognizer,
    stream: AudioStreamer,
    lang: str,
    codec: str,
    filepath: str,
):

    # Shortcuts
    send = socket.send

    def expect(*event_classes):
        event = client.receive(socket.recv())
        assert isinstance(event, event_classes), f"expected {event_classes} got {event}"
        return event

    # scenario

    send(client.open("mytest", audio_codec=codec))
    expect(Opened)
    stream.start()

    send(
        client.set_params(
            speech_language=lang, no_input_timeout=5000, recognition_timeout=20000
        )
    )
    expect(ParamsSet)

    # Recognize address
    stream.play(filepath, codec)
    send(
        client.recognize(
            "builtin:speech/text2num",
            speech_complete_timeout=1200,
        )
    )
    expect(RecognitionInProgress)

    expect(StartOfInput)
    event = expect(RecognitionComplete)
    cc = event.completion_cause
    result = event.body
    if cc == CC.Success:
        print("Got transcription:", result.nlu.value)
    else:
        print(cc)
        if result.asr:
            print("Error but got", result.asr.transcript)
        else:
            print("No transcript")

    stream.skip()
    stream.stop()
    send(client.close())
    expect(Closed)


if __name__ == "__main__":
    import argparse

    uhlive_client = os.environ["UHLIVE_API_CLIENT"]
    uhlive_secret = os.environ["UHLIVE_API_SECRET"]
    parser = argparse.ArgumentParser(
        description="Get the transcription of an audio file, live!"
    )
    parser.add_argument("audio_file", help="Audio file to transcribe")
    parser.add_argument("--language", dest="lang", default="fr")
    parser.add_argument("--audio_codec", dest="codec", default="linear")
    args = parser.parse_args()
    auth_url, auth_params = build_authentication_request(uhlive_client, uhlive_secret)
    login = requests.post(auth_url, data=auth_params)
    login.raise_for_status()
    uhlive_token = login.json()["access_token"]

    url, headers = build_connection_request(uhlive_token)
    socket = ws.create_connection(url, header=headers)
    client = Recognizer()
    stream = AudioStreamer(socket, client)
    try:
        main(socket, client, stream, args.lang, args.codec, args.audio_file)
    finally:
        stream.stop()
        stream.join()
        socket.close()
