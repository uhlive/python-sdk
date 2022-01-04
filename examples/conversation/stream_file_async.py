import asyncio
import time

from aiohttp import ClientSession  # type: ignore

from uhlive.stream.conversation import Conversation, Ok, build_conversation_url


async def stream_file(audio_path, socket, client):
    with open(audio_path, "rb") as audio_file:
        while True:
            audio_chunk = audio_file.read(8000)
            if not audio_chunk:
                break
            # audio is sent as binary frames
            await socket.send_bytes(client.send_audio_chunk(audio_chunk))
            await asyncio.sleep(0.5)  # Simulate real time audio
    print(f"File {audio_path} successfully streamed")
    await socket.send_str(client.leave())


async def main(uhlive_url, uhlive_token, uhlive_id, cmdline_args):
    async with ClientSession() as session:
        async with session.ws_connect(
            build_conversation_url(uhlive_url, uhlive_token)
        ) as socket:
            client = Conversation(uhlive_id, cmdline_args.conversation_id, "Alice")
            # shortcut
            await socket.send_str(
                client.join(
                    model=cmdline_args.model,
                    interim_results=cmdline_args.interim_results,
                    rescoring=cmdline_args.rescoring,
                    origin=int(time.time() * 1000),
                    country=cmdline_args.country,
                    codec=cmdline_args.codec,
                )
            )
            # check we didn't get an error on join
            msg = await socket.receive()
            client.receive(msg.data)

            streamer = asyncio.create_task(
                stream_file(cmdline_args.audio_file, socket, client)
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
    parser.add_argument("--codec", dest="codec", default="linear")
    parser.add_argument("--country", dest="country", default="fr")
    parser.add_argument(
        "--without_interim_results",
        dest="interim_results",
        action="store_false",
    )
    parser.add_argument("--without_rescoring", dest="rescoring", action="store_false")
    args = parser.parse_args()

    uhlive_url = os.environ["UHLIVE_API_URL"]
    uhlive_token = os.environ["UHLIVE_API_TOKEN"]
    uhlive_id = os.environ["UHLIVE_API_ID"]
    asyncio.run(main(uhlive_url, uhlive_token, uhlive_id, args))
