import asyncio
import time

from aiohttp import ClientSession  # type: ignore

from uhlive.auth import build_authentication_request
from uhlive.stream.conversation import Conversation, Ok, build_conversation_url


async def stream_file(audio_path, socket, client, codec):
    chunk_size = 4000 if codec.startswith("g711") else 8000
    with open(audio_path, "rb") as audio_file:
        while True:
            audio_chunk = audio_file.read(chunk_size)
            if not audio_chunk:
                break
            # audio is sent as binary frames
            await socket.send_bytes(client.send_audio_chunk(audio_chunk))
            await asyncio.sleep(0.5)  # Simulate real time audio
    print(f"File {audio_path} successfully streamed")
    await socket.send_str(client.leave())


async def main(uhlive_client, uhlive_secret, cmdline_args):
    async with ClientSession() as session:
        auth_url, auth_params = build_authentication_request(
            uhlive_client, uhlive_secret, args.user_id, args.user_pwd
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
                    audio_codec=cmdline_args.codec,
                )
            )
            join = time.time()
            # check we didn't get an error on join
            msg = await socket.receive()
            print(
                "join resp =",
                client.receive(msg.data),
                "in",
                time.time() - join,
                "seconds",
            )

            streamer = asyncio.create_task(
                stream_file(cmdline_args.audio_file, socket, client, cmdline_args.codec)
            )
            print("Listening…")
            try:
                while True:
                    msg = await socket.receive()
                    event = client.receive(msg.data)
                    if client.left:
                        break
                    if not isinstance(event, Ok):
                        print(event)
            finally:
                streamer.cancel()
                await streamer


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Get the transcription of an audio file, live!"
    )
    parser.add_argument("audio_file", help="Audio file to transcribe")
    parser.add_argument("conversation_id", help="Conversation ID")
    parser.add_argument("--asr_model", dest="model", default="fr")
    parser.add_argument("--audio_codec", dest="codec", default="linear")
    parser.add_argument("--country", dest="country", default="fr")
    parser.add_argument(
        "--without_interim_results",
        dest="interim_results",
        action="store_false",
    )
    parser.add_argument("--without_rescoring", dest="rescoring", action="store_false")
    parser.add_argument("--user", dest="user_id", default="")
    parser.add_argument("--password", dest="user_pwd", default="")

    args = parser.parse_args()

    uhlive_client = os.environ["UHLIVE_API_CLIENT"]
    uhlive_secret = os.environ["UHLIVE_API_SECRET"]
    asyncio.run(main(uhlive_client, uhlive_secret, args))
