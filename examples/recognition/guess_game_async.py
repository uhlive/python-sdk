import asyncio
import os
from random import randint

import sounddevice as sd  # type: ignore
from aiohttp import ClientSession  # type: ignore

from uhlive.auth import build_authentication_request
from uhlive.stream.recognition import (
    CompletionCause,
    GrammarDefined,
    Opened,
    ParamsSet,
    RecognitionComplete,
    RecognitionInProgress,
    Recognizer,
    StartOfInput,
    build_connection_request,
)


async def inputstream_generator(channels=1, samplerate=8000, dtype="int16", **kwargs):
    """Generator that yields blocks of input data as NumPy arrays."""
    q_in = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def callback(indata, frame_count, time_info, status):
        loop.call_soon_threadsafe(q_in.put_nowait, bytes(indata))

    stream = sd.RawInputStream(
        callback=callback,
        channels=channels,
        samplerate=samplerate,
        dtype=dtype,
        **kwargs,
    )
    with stream:
        while True:
            indata = await q_in.get()
            yield indata


async def play_prompt(text):
    print(text)
    # let time to read it
    await asyncio.sleep(len(text.split()) * 0.1)


async def stream(socket, client):
    try:
        async for block in inputstream_generator(blocksize=960):
            await socket.send_bytes(client.send_audio_chunk(block))
    except asyncio.CancelledError:
        pass


async def main(uhlive_client: str, uhlive_secret: str):
    # create transport
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
            # instantiate service
            client = Recognizer()
            # Open a session
            # Commands are sent as text frames
            await socket.send_str(client.open())
            # Check if successfull
            msg = await socket.receive()
            event = client.receive(msg.data)
            assert isinstance(event, Opened), f"Expected Opened, got {event}"
            # start streaming the user's voice
            voice = asyncio.create_task(stream(socket, client))
            await socket.send_str(
                client.set_params(
                    speech_language="en",  # or "fr"
                    no_input_timeout=5000,
                    speech_complete_timeout=1000,
                    speech_incomplete_timeout=2000,
                    speech_nomatch_timeout=3000,
                    recognition_timeout=30000,
                )
            )
            # Check if successfull
            msg = await socket.receive()
            event = client.receive(msg.data)
            assert isinstance(event, ParamsSet), f"Expected ParamsSet, got {event}"
            await socket.send_str(
                client.define_grammar(
                    "speech/spelling/digits?regex=[0-9]{1,2}", "num_in_range100"
                )
            )
            # Check if successful
            msg = await socket.receive()
            event = client.receive(msg.data)
            assert isinstance(
                event, GrammarDefined
            ), f"Expected GrammarDefined, got {event}"
            send = socket.send_str

            async def expect(*event_classes):
                msg = await socket.receive()
                event = client.receive(msg.data)
                assert isinstance(
                    event, event_classes
                ), f"expected {event_classes} got {event}"
                return event

            play_again = True
            while play_again:
                secret = randint(0, 99)
                await play_prompt(
                    "I chose a number between 0 and 99. Try to guess it in less than five turns."
                )
                for i in range(1, 6):
                    await play_prompt(f"Turn {i}: what's your guess?")
                    await send(client.recognize("session:num_in_range100"))
                    await expect(RecognitionInProgress)
                    response = await expect(RecognitionComplete, StartOfInput)
                    if isinstance(response, StartOfInput):
                        response = await expect(RecognitionComplete)
                    if response.completion_cause == CompletionCause.NoInputTimeout:
                        await play_prompt(
                            "You should answer faster, you loose your turn!"
                        )
                        continue
                    if response.completion_cause != CompletionCause.Success:
                        print(response)
                        got = response.body.asr.transcript or response.completion_cause
                        await play_prompt(
                            f"{got} is not a number between 0 and 99. You lose your turn."
                        )
                        continue
                    # It's safe to access the NLU value now
                    guess = int(response.body.nlu.value)
                    if guess == secret:
                        await play_prompt("You win! Congratulations!")
                        break
                    elif guess > secret:
                        await play_prompt("Your guess is too high")
                    else:
                        await play_prompt("Your guess is too low")
                else:
                    await play_prompt(f"You lose! My secret number was {secret}.")
                while True:
                    await play_prompt("Do you want to play again?")
                    await send(
                        client.recognize(
                            "builtin:speech/boolean", recognition_mode="hotword"
                        )
                    )
                    await expect(RecognitionInProgress)
                    # No StartOfInput in hotword mode
                    response = await expect(RecognitionComplete)
                    if response.completion_cause != CompletionCause.Success:
                        await play_prompt("Please, clearly answer the question.")
                        continue
                    play_again = response.body.nlu.value
                    break
            voice.cancel()
            await voice
            await send(client.close())


if __name__ == "__main__":
    uhlive_client = os.environ["UHLIVE_API_CLIENT"]
    uhlive_secret = os.environ["UHLIVE_API_SECRET"]
    asyncio.run(main(uhlive_client, uhlive_secret))
