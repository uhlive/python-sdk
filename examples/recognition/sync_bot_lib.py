"""Mini Bot Framework (French), async version

This code is provided as-is for demonstration purposes only and is not
suitable for production. Use at your own risk.
"""
import base64
from typing import Dict

import requests
import sounddevice as sd  # type: ignore
import websocket as ws  # type: ignore

from uhlive.auth import build_authentication_request
from uhlive.stream.recognition import Closed
from uhlive.stream.recognition import CompletionCause as CC
from uhlive.stream.recognition import (
    DefaultParams,
    GrammarDefined,
    Opened,
    ParamsSet,
    RecognitionComplete,
    RecognitionInProgress,
    Recognizer,
    StartOfInput,
    build_connection_request,
)


class Bot:
    TTF_CACHE: Dict[str, bytes] = {}

    def __init__(self, google_ttf_key):
        self.client = Recognizer()
        self.socket = None
        self.google_ttf_key = google_ttf_key

    def stream_mic(self):
        def callback(indata, frame_count, time_info, status):
            self.socket.send_binary(bytes(indata))

        stream = sd.RawInputStream(
            callback=callback, channels=1, samplerate=8000, dtype="int16", blocksize=960
        )
        stream.start()
        return stream

    def _ttf(self, text) -> bytes:
        if text in self.TTF_CACHE:
            return self.TTF_CACHE[text]
        payload = {
            "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 8000},
            "input": {"text": text},
            "voice": {"languageCode": "fr-FR", "name": "fr-FR-Wavenet-C"},
        }
        # url = "https://texttospeech.googleapis.com/v1/text:synthesize"
        url = f"https://texttospeech.googleapis.com/v1beta1/text:synthesize?key={self.google_ttf_key}"
        h = {"Content-Type": "application/json; charset=utf-8"}
        response = requests.post(url, headers=h, json=payload)
        response.raise_for_status()
        json = response.json()
        audio = base64.b64decode(json["audioContent"])[44:]
        self.TTF_CACHE[text] = audio
        return audio

    def say(self, text):
        audio = self._ttf(text)
        with sd.RawOutputStream(
            channels=1,
            samplerate=8000,
            dtype="int16",
        ) as stream:
            stream.write(audio)
        print("à vous")

    def expect(self, *event_classes, ignore=None):
        while True:
            event = self.client.receive(self.socket.recv())
            if isinstance(event, event_classes):
                return event
            elif ignore is None or not isinstance(event, ignore):
                raise AssertionError(f"Expected one of {event_classes}, got {event}")

    def ask_until_success(self, text, *args, **kwargs):
        choice = None
        while choice is None:
            self.say(text)
            self.socket.send(self.client.recognize(*args, **kwargs))
            self.expect(RecognitionInProgress)
            resp = self.expect(RecognitionComplete, ignore=(StartOfInput,))
            if resp.completion_cause == CC.Success:
                choice = resp.body.nlu
            else:
                if resp.body.asr:
                    self.say("Je n'ai pas compris")
                    print("user said:", resp.body.asr.transcript)
                else:
                    self.say("Je n'ai rien entendu")
        return choice

    def confirm(self, text: str) -> bool:
        res = self.ask_until_success(
            text,
            "builtin:speech/boolean",
            recognition_mode="hotword",
            hotword_max_duration=5000,
        )
        return res.value

    def run(self, uhlive_client: str, uhlive_secret: str):
        auth_url, auth_params = build_authentication_request(
            uhlive_client, uhlive_secret
        )
        login = requests.post(auth_url, data=auth_params)
        login.raise_for_status()
        uhlive_token = login.json()["access_token"]

        url, headers = build_connection_request(uhlive_token)
        self.socket = socket = ws.create_connection(url, header=headers)
        try:
            self.socket = socket
            socket.send(self.client.open("deskbot"))
            self.expect(Opened)
            streamer = self.stream_mic()
            try:
                self.scenario()
            except Exception as e:
                self.say("Nous subissons une avarie. Rappelez plus tard.")
                raise e
            finally:
                streamer.stop()
                streamer.close()
                socket.send(self.client.close())
                self.expect(Closed)
        finally:
            socket.close()

    def set_params(self, **kwargs):
        self.socket.send(self.client.set_params(**kwargs))
        self.expect(ParamsSet)

    def get_params(self):
        self.socket.send(self.client.get_params())
        res = self.expect(DefaultParams)
        return res

    def define_grammar(self, builtin, alias):
        self.socket.send(self.client.define_grammar(builtin, alias))
        self.expect(GrammarDefined)

    def recognize(self, *args, **kwargs):
        self.socket.send(self.client.recognize(*args, **kwargs))
        self.expect(RecognitionInProgress)

    def scenario(self):
        """To be overridden in subclasses"""
        raise NotImplementedError
