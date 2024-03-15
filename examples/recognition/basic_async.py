import asyncio
import os

from aiohttp import ClientSession  # type: ignore

from uhlive.auth import build_authentication_request
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
    build_connection_request,
)


async def stream(socket, client, audio_files):
    try:
        for audio in audio_files:
            print(f"Streaming file in realtime: {audio} for transcription!")
            audio_file = open(audio, "rb")
            while True:
                audio_chunk = audio_file.read(960)
                if not audio_chunk:
                    break
                await socket.send_bytes(client.send_audio_chunk(audio_chunk))
                await asyncio.sleep(0.06)

            print(f"File {audio} successfully streamed")
            audio_file.close()
        # stream silence
        while True:
            await socket.send_bytes(client.send_audio_chunk(bytes(960)))
            await asyncio.sleep(0.06)
    except asyncio.CancelledError:
        pass


async def main(uhlive_url: str, uhlive_token: str):
    async with ClientSession() as session:
        auth_url, auth_params = build_authentication_request(
            uhlive_client, uhlive_secret
        )
        async with session.post(auth_url, data=auth_params) as login:
            login.raise_for_status()
            body = await login.json()
            uhlive_token = body["access_token"]

        url, headers = build_connection_request(uhlive_token)
        async with session.ws_connect(url, headers=headers) as socket:
            client = Recognizer()

            # Shortcuts
            send = socket.send_str

            async def expect(*event_classes):
                msg = await socket.receive()
                event = client.receive(msg.data)
                assert isinstance(
                    event, event_classes
                ), f"expected {event_classes} got {event}"
                return event

            # Scenario

            await send(client.open("mytest", session_id="mysession"))
            await expect(Opened)
            # start streaming
            streamer = asyncio.create_task(
                stream(
                    socket,
                    client,
                    ("fixtures/fr_address_ok.pcm", "fixtures/parcel_number.pcm"),
                )
            )

            await send(
                client.set_params(
                    speech_language="fr",
                    no_input_timeout=5000,
                    logging_tag="basic_async_test",
                )
            )
            await expect(ParamsSet)

            # Recognize address
            await send(
                client.recognize(
                    "builtin:speech/postal_address",
                    speech_complete_timeout=800,
                    no_input_timeout=5000,
                )
            )
            await expect(RecognitionInProgress)

            await expect(StartOfInput)
            event = await expect(RecognitionComplete)
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

            # Recognize parcel number
            await send(
                client.define_grammar(
                    "speech/spelling/mixed?regex=[a-z]{2}[0-9]{9}[a-z]{2}", "parcel"
                )
            )
            await expect(GrammarDefined)

            await send(
                client.recognize(
                    "session:parcel",
                    hotword_max_duration=10000,
                    no_input_timeout=5000,
                    recognition_mode="hotword",
                )
            )
            await expect(RecognitionInProgress)

            event = await expect(RecognitionComplete)
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

            streamer.cancel()
            await streamer
            await send(client.close())
            await expect(Closed)


if __name__ == "__main__":
    uhlive_client = os.environ["UHLIVE_API_CLIENT"]
    uhlive_secret = os.environ["UHLIVE_API_SECRET"]
    asyncio.run(main(uhlive_client, uhlive_secret))
