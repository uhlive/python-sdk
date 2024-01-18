"""Mini Bot Framework (French), async version

This code is provided as-is for demonstration purposes only and is not
suitable for production. Use at your own risk.
"""
import asyncio
import base64
from typing import Dict

import sounddevice as sd  # type: ignore
from aiohttp import ClientSession  # type: ignore

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


async def play_buffer(buffer, channels=1, samplerate=8000, dtype="int16", **kwargs):
    loop = asyncio.get_event_loop()
    event = asyncio.Event()
    idx = 0

    def callback(outdata, frame_count, time_info, status):
        nonlocal idx
        bcount = frame_count * 2
        if status:
            print(status)
        remainder = len(buffer) - idx
        if remainder == 0:
            loop.call_soon_threadsafe(event.set)
            raise sd.CallbackStop
        valid_frames = bcount if remainder >= bcount else remainder
        outdata[:valid_frames] = buffer[idx : idx + valid_frames]
        idx += valid_frames

    stream = sd.RawOutputStream(
        callback=callback,
        dtype=dtype,
        samplerate=samplerate,
        channels=channels,
        **kwargs,
    )
    with stream:
        await event.wait()


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


class Bot:
    TTF_CACHE: Dict[str, bytes] = {}

    def __init__(self, google_ttf_key):
        self.client = Recognizer()
        self.session = None
        self.socket = None
        self.google_ttf_key = google_ttf_key

    async def stream_mic(self):
        try:
            async for block in inputstream_generator(blocksize=960):
                await self.socket.send_bytes(self.client.send_audio_chunk(block))
        except asyncio.CancelledError:
            pass

    async def _ttf(self, text) -> bytes:
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
        async with self.session.post(url, headers=h, json=payload) as response:
            json = await response.json()
            audio = base64.b64decode(json["audioContent"])[44:]
            self.TTF_CACHE[text] = audio
            return audio

    async def say(self, text):
        audio = await self._ttf(text)
        await play_buffer(audio)

    async def expect(self, *event_classes, ignore=None):
        while True:
            msg = await self.socket.receive()
            event = self.client.receive(msg.data)
            if isinstance(event, event_classes):
                return event
            elif ignore is None or not isinstance(event, ignore):
                raise AssertionError(f"Expected one of {event_classes}, got {event}")

    async def ask_until_success(self, text, *args, **kwargs):
        choice = None
        while choice is None:
            await self.say(text)
            await self.socket.send_str(self.client.recognize(*args, **kwargs))
            await self.expect(RecognitionInProgress)
            resp = await self.expect(RecognitionComplete, ignore=(StartOfInput,))
            if resp.completion_cause == CC.Success:
                choice = resp.body.nlu
            else:
                if resp.body.asr:
                    await self.say("Je n'ai pas compris")
                    print("user said:", resp.body.asr.transcript)
                else:
                    await self.say("Je n'ai rien entendu")
        return choice

    async def confirm(self, text: str) -> bool:
        res = await self.ask_until_success(
            text,
            "builtin:speech/boolean",
            recognition_mode="hotword",
            hotword_max_duration=5000,
        )
        return res.value

    async def run(self, uhlive_client: str, uhlive_secret: str):
        async with ClientSession() as session:
            self.session = session
            auth_url, auth_params = build_authentication_request(
                uhlive_client, uhlive_secret
            )
            async with session.post(auth_url, data=auth_params) as login:
                login.raise_for_status()
                body = await login.json()
                uhlive_token = body["access_token"]

            url, headers = build_connection_request(uhlive_token)
            async with session.ws_connect(url, headers=headers) as socket:
                self.socket = socket
                await socket.send_str(self.client.open("deskbot"))
                await self.expect(Opened)
                streamer = asyncio.create_task(self.stream_mic())
                try:
                    await self.scenario()
                except Exception as e:
                    await self.say("Nous subissons une avarie. Rappelez plus tard.")
                    raise e
                finally:
                    streamer.cancel()
                    await streamer
                    await socket.send_str(self.client.close())
                    await self.expect(Closed)

    async def set_params(self, **kwargs):
        await self.socket.send_str(self.client.set_params(**kwargs))
        await self.expect(ParamsSet)

    async def get_params(self):
        await self.socket.send_str(self.client.get_params())
        res = await self.expect(DefaultParams)
        return res

    async def define_grammar(self, builtin, alias):
        await self.socket.send_str(self.client.define_grammar(builtin, alias))
        await self.expect(GrammarDefined)

    async def recognize(self, *args, **kwargs):
        await self.socket.send_str(self.client.recognize(*args, **kwargs))
        await self.expect(RecognitionInProgress)

    async def scenario(self):
        """To be overridden in subclasses"""
        raise NotImplementedError
