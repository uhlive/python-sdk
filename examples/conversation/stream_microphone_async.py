import asyncio
import time

import sounddevice as sd  # type: ignore
from aiohttp import ClientSession  # type: ignore

from uhlive.auth import build_authentication_request
from uhlive.stream.conversation import Conversation, Ok, build_conversation_url


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


async def stream_mic(socket, client):
    try:
        async for block in inputstream_generator(blocksize=960):
            await socket.send_bytes(client.send_audio_chunk(block))
    except asyncio.CancelledError:
        pass


async def main(uhlive_client, uhlive_secret, cmdline_args):
    async with ClientSession() as session:
        auth_url, auth_params = build_authentication_request(
            uhlive_client, uhlive_secret
        )
        async with session.post(auth_url, data=auth_params) as login:
            login.raise_for_status()
            body = await login.json()
            uhlive_token = body["access_token"]

        async with session.ws_connect(build_conversation_url(uhlive_token)) as socket:
            client = Conversation(uhlive_client, cmdline_args.conversation_id, "Alice")
            # shortcut
            await socket.send_str(
                client.join(
                    model=cmdline_args.model,
                    interim_results=cmdline_args.interim_results,
                    rescoring=cmdline_args.rescoring,
                    origin=int(time.time() * 1000),
                    country=cmdline_args.country,
                )
            )
            # check we didn't get an error on join
            msg = await socket.receive()
            client.receive(msg.data)

            streamer = asyncio.create_task(stream_mic(socket, client))
            print("Listening…")
            try:
                while True:
                    try:
                        msg = await socket.receive()
                        event = client.receive(msg.data)
                    except KeyboardInterrupt:
                        break
                    if not isinstance(event, Ok):
                        print(event)
            finally:
                streamer.cancel()
                await streamer
                await socket.send_str(client.leave())


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Get the transcription of an audio file, live!"
    )
    parser.add_argument("conversation_id", help="Conversation ID")
    parser.add_argument("--asr_model", dest="model", default="fr")
    parser.add_argument("--country", dest="country", default="fr")
    parser.add_argument(
        "--without_interim_results",
        dest="interim_results",
        action="store_false",
    )
    parser.add_argument("--without_rescoring", dest="rescoring", action="store_false")
    args = parser.parse_args()

    uhlive_client = os.environ["UHLIVE_API_CLIENT"]
    uhlive_secret = os.environ["UHLIVE_API_SECRET"]
    asyncio.run(main(uhlive_client, uhlive_secret, args))
