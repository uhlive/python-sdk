import os
import time
from random import randint

import sounddevice as sd  # type: ignore
import websocket as ws  # type: ignore

from uhlive.stream.recognition import (
    CompletionCause,
    GrammarDefined,
    Opened,
    ParamsSet,
    RecognitionComplete,
    RecognitionInProgress,
    Recognizer,
    StartOfInput,
)


def play_prompt(text):
    print(text)
    # let time to read it
    time.sleep(len(text.split()) * 0.1)


def stream_mic(socket, client):
    def callback(indata, frame_count, time_info, status):
        socket.send_binary(bytes(indata))

    stream = sd.RawInputStream(
        callback=callback, channels=1, samplerate=8000, dtype="int16", blocksize=960
    )
    stream.start()
    return stream


def main(uhlive_url: str, uhlive_token: str):
    # create transport
    socket = ws.create_connection(
        uhlive_url, header={"Authorization": f"bearer {uhlive_token}"}
    )
    # instantiate service
    client = Recognizer()
    # Open a session
    # Commands are sent as text frames
    socket.send(client.open())
    # Check if successfull
    event = client.receive(socket.recv())
    assert isinstance(event, Opened), f"Expected Opened, got {event}"
    # start streaming the user's voice
    voice = stream_mic(socket, client)
    voice.start()
    socket.send(
        client.set_params(
            speech_language="en",  # or "fr"
            no_input_timeout=5000,
            speech_complete_timeout=1000,
            speech_incomplete_timeout=2000,
            speech_nomatch_timeout=3000,
            recognition_timeout=30000,
        )
    )
    # Check if successful
    event = client.receive(socket.recv())
    assert isinstance(event, ParamsSet), f"Expected ParamsSet, got {event}"
    socket.send(
        client.define_grammar(
            "speech/spelling/digits?regex=[0-9]{1,2}", "num_in_range100"
        )
    )
    # Check if successful
    event = client.receive(socket.recv())
    assert isinstance(event, GrammarDefined), f"Expected ParamsSet, got {event}"
    send = socket.send

    def expect(*event_classes):
        event = client.receive(socket.recv())
        assert isinstance(event, event_classes), f"Expected {event_classes} got {event}"
        return event

    play_again = True
    while play_again:
        secret = randint(0, 99)
        play_prompt(
            "I chose a number between 0 and 99. Try to guess it in less than five turns."
        )
        for i in range(1, 6):
            play_prompt(f"Turn {i}: what's your guess?")
            send(client.recognize("session:num_in_range100"))
            expect(RecognitionInProgress)
            response = expect(RecognitionComplete, StartOfInput)
            if isinstance(response, StartOfInput):
                response = expect(RecognitionComplete)
            if response.completion_cause == CompletionCause.NoInputTimeout:
                play_prompt("You should answer faster, you loose your turn!")
                continue
            if response.completion_cause != CompletionCause.Success:
                play_prompt("That's not a number between 0 and 99. You lose your turn.")
                continue
            # It's safe to access the NLU value now
            guess = int(response.body.nlu.value)
            if guess == secret:
                play_prompt("You win! Congratulations!")
                break
            elif guess > secret:
                play_prompt("Your guess is too high")
            else:
                play_prompt("Your guess is too low")
        else:
            play_prompt(f"You lose! My secret number was {secret}.")
        while True:
            play_prompt("Do you want to play again?")
            send(client.recognize("builtin:speech/boolean", recognition_mode="hotword"))
            expect(RecognitionInProgress)
            # No StartOfInput in hotword mode
            response = expect(RecognitionComplete)
            if response.completion_cause != CompletionCause.Success:
                play_prompt("Please, clearly answer the question.")
                continue
            play_again = response.body.nlu.value
            break
    voice.stop()
    send(client.close())
    socket.close()


if __name__ == "__main__":
    uhlive_url = os.environ["UHLIVE_API_URL"]
    uhlive_token = os.environ["UHLIVE_API_TOKEN"]
    main(uhlive_url, uhlive_token)
