import asyncio
from pathlib import Path
from time import time
from typing import Any, Dict, List, Optional, Sequence

import toml  # type: ignore
from aiohttp import ClientSession  # type: ignore

from uhlive.auth import build_authentication_request
from uhlive.stream.recognition import (
    Closed,
    CompletionCause,
    Event,
    Interpretation,
    Opened,
    RecognitionComplete,
    RecognitionInProgress,
    Recognizer,
    StartOfInput,
    build_connection_request,
)

CODEC_HINTS = {"linear": (960, 0), "g711a": (480, 0x55), "g711u": (480, 0xFF)}


class Expectation:
    def __init__(
        self, status: CompletionCause, result: Optional[Interpretation]
    ) -> None:
        self.completion_cause = status
        self.result = result

    def __str__(self) -> str:
        return f"<{self.completion_cause} — {self.result}>"


class RecognitionFailed(RuntimeError):
    def __init__(self, expected: Expectation, got: Event):
        if not isinstance(got, RecognitionComplete):
            message = f"Unexpected event {got}"
        else:
            mparts = []
            if expected.completion_cause != got.completion_cause:
                mparts.append(
                    f"- Expected status: {expected.completion_cause},"
                    f" got {got.completion_cause} ({got.completion_reason})"
                )
            if got.body is not None and expected.result != got.body.nlu:
                mparts.append(
                    f"- Expected result: {expected.result}\n- got:             {got.body.nlu}"
                )
            if got.body:
                mparts.append(f"- Raw ASR:         {got.body.asr}")
            message = "\n".join(mparts)
        super().__init__(message)
        self.expected = expected
        self.got = got

    def is_expected_cause(self):
        return self.expected.completion_cause == self.got.completion_cause


class Report:
    def __init__(self, passed, failed, partial, errors, skipped, failures):
        self.passed = passed
        self.failed = failed
        self.partial = partial
        self.errors = errors
        self.skipped = skipped
        self.failures = failures

    @classmethod
    def merge(cls, *reports):
        passed = 0
        failed = 0
        partial = 0
        errors = 0
        skipped = 0
        failures = []
        for r in reports:
            passed += r.passed
            failed += r.failed
            partial += r.partial
            errors += r.errors
            skipped += r.skipped
            failures.extend(r.failures)
        return cls(passed, failed, partial, errors, skipped, failures)

    def total(self):
        return self.passed + self.failed + self.errors + self.skipped


def init_bytes(size, value):
    return bytes([value]) * size


async def stream(socket, client, audio_path, codec="linear"):
    chunk_size, silence_value = CODEC_HINTS[codec]
    silence = init_bytes(chunk_size, silence_value)
    try:
        audio_file = open(audio_path, "rb")
        while True:
            audio_chunk = audio_file.read(chunk_size)
            if not audio_chunk:
                break
            await socket.send_bytes(client.send_audio_chunk(audio_chunk))
            await asyncio.sleep(0.059)

        audio_file.close()
        # stream silence
        while True:
            await socket.send_bytes(client.send_audio_chunk(silence))
            await asyncio.sleep(0.059)
    except asyncio.CancelledError:
        # Stream 1 second silence to purge.
        for _ in range(15):
            await socket.send_bytes(client.send_audio_chunk(silence))
            await asyncio.sleep(0.059)


class TestRunner:
    def __init__(self, fixture_folder: str) -> None:
        self.fixtures = Path(fixture_folder).resolve()
        self.socket = None
        self.client = Recognizer()
        self.codec = "linear"

    async def expect(self, *event_classes, ignore=None) -> Event:
        assert self.socket is not None  # to please mypy
        while True:
            msg = await self.socket.receive()
            event = self.client.receive(msg.data)
            if isinstance(event, event_classes):
                return event
            elif ignore is None or not isinstance(event, ignore):
                raise AssertionError(f"Expected one of {event_classes}, got {event}")

    async def check(
        self,
        audio_file: Path,
        grammars: Sequence[str],
        params: Dict[str, Any],
        expected: Expectation,
    ) -> None:
        """Raise an exception if the test fails."""
        assert self.socket is not None  # to please mypy
        ext = audio_file.suffix[1:]
        if ext == "pcm":
            ext = "linear"
        if ext != self.codec:
            self.codec = ext
            await self.socket.send_str(self.client.close())
            await self.expect(Closed)
            await self.socket.send_str(
                self.client.open("testsuite", audio_codec=self.codec)
            )
            await self.expect(Opened)

        streamer = asyncio.create_task(
            stream(self.socket, self.client, audio_file, ext)
        )
        await self.socket.send_str(self.client.recognize(*grammars, **params))
        # TODO: we may want to test StartOfInput accuracy
        try:
            await self.expect(RecognitionInProgress)
            if (
                params["recognition_mode"] == "normal"
                and expected.completion_cause != CompletionCause.NoInputTimeout
            ):
                await self.expect(StartOfInput)
            event = await self.expect(RecognitionComplete)
            assert event.body is not None, "Got unexpected empty body"
            if event.completion_cause == expected.completion_cause:
                nlu = event.body.nlu
                if nlu is None and expected.result is None:
                    return
                if (
                    nlu is not None
                    and expected.result is not None
                    and (
                        nlu.type == expected.result.type
                        and nlu.value == expected.result.value
                    )
                ):
                    return
            raise RecognitionFailed(expected, event)
        finally:
            streamer.cancel()
            await streamer

    async def walk_tests(
        self, files: Sequence[Path], overrides: Dict[str, Any], honor_skipped: bool
    ):
        nb_tests = len(files)
        passed = 0
        failed = 0
        errors = 0
        skipped = 0
        partial = 0
        failures = []
        for i, test_conf in enumerate(files, 1):
            prompt = f"{i}/{nb_tests} — {test_conf.name}:"
            test = toml.load(test_conf)
            if test.get("skip", False) and honor_skipped:
                print("skipped")
                skipped += 1
                continue
            if overrides:
                test["params"].update(overrides)
            try:
                nlu_desc = test["expected"].get("interpretation")
                if nlu_desc:
                    if "confidence" not in nlu_desc:
                        nlu_desc[
                            "confidence"
                        ] = 0.5  # ignored anyway, but expected by Interpretation
                    interpretation: Optional[Interpretation] = Interpretation(nlu_desc)
                else:
                    interpretation = None
                expected = Expectation(
                    CompletionCause(test["expected"]["completion_cause"]),
                    interpretation,
                )
                await self.check(
                    self.fixtures / test["audio"],
                    test["grammars"],
                    test["params"],
                    expected,
                )
            except RecognitionFailed as e:
                failures.append((test_conf, e))
                failed += 1
                if e.is_expected_cause():
                    print(prompt, "\033[33m partial\033[0m")
                    partial += 1
                else:
                    print(prompt, "\033[91m failed\033[0m")
            except Exception as e:
                print(prompt, "\033[93m error\033[0m")
                print("unable to run test:", e)
                errors += 1
            else:
                passed += 1
                print(prompt, "\033[92m passed\033[0m")
        return Report(passed, failed, partial, errors, skipped, failures)

    async def run(
        self,
        uhlive_client: str,
        uhlive_secret: str,
        files: Sequence[Path],
        overrides: Dict[str, Any],
        honor_skipped: bool,
    ):
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
                self.socket = socket  # type: ignore
                await socket.send_str(self.client.open("testsuite"))
                await self.expect(Opened)
                report = await self.walk_tests(files, overrides, honor_skipped)
                await socket.send_str(self.client.close())
                await self.expect(Closed)
        return report


if __name__ == "__main__":
    import argparse
    import os

    test_file_format = """The .test files are in the toml format and describe the tests to run. For example:

# Sample test file

# The audio that will be streamed
audio = "parcel_number.pcm"
# The list of grammars to match
# Most of the time, only one grammar is specified
grammars = [
    "builtin:speech/spelling/mixed?regex=[a-z]{2}[0-9]{9}[a-z]{2}"
]

# The recognition parameters to set
[params]
speech_language = "fr"
hotword_max_time = 10000
no_input_timeout = 5000
recognition_mode = "hotword"

# The expected results
[expected]
completion_cause = "Success"

[expected.interpretation]
# The URI (without the query string) of the grammar that should match
type = "builtin:speech/spelling/mixed"
# The interpretation value we should get
value = "le137137866cn"
"""
    parser = argparse.ArgumentParser(
        description="Run recogntion tests in .test files",
        epilog=test_file_format,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "test_folder", help="path to the folder where the test files are"
    )
    parser.add_argument(
        "--tests",
        nargs="*",
        help="process individual test files relative to `test_folder`. If missing, all test files in the `test_folder` are processed.",
    )
    parser.add_argument("--concurrency", type=int, default=1, help="Concurrency level")
    parser.add_argument("--overrides", nargs="*", help="parameters to override")
    args = parser.parse_args()
    uhlive_client = os.environ["UHLIVE_API_CLIENT"]
    uhlive_secret = os.environ["UHLIVE_API_SECRET"]
    overrides = {}
    for override in args.overrides or []:
        param, value = override.split("=")
        if value.isdigit():
            value = int(value)
        overrides[param] = value
    try:
        import uvloop  # type: ignore

        uvloop.install()
        print("Using high perf uvloop")
    except ImportError:
        print("Using builtin asyncio")
    # Gather files
    files: List[Path]
    if not args.tests:
        files = list(Path(args.test_folder).glob("*.test"))
        honor_skipped = True
    else:
        files = [Path(args.test_folder) / path for path in args.tests]
        honor_skipped = False

    # partition tests
    concurrency = min(args.concurrency, len(files))
    print("Concurrency =", concurrency)
    tasks = []
    for i in range(concurrency):
        print("Preparing task to run tests", files[i::concurrency])
        runner = TestRunner(args.test_folder)
        tasks.append(
            runner.run(
                uhlive_client,
                uhlive_secret,
                files[i::concurrency],
                overrides,
                honor_skipped,
            )
        )

    start = time()

    async def run_all():
        res = await asyncio.gather(*tasks)
        return res

    report = Report.merge(*asyncio.run(run_all()))
    print("=============")
    print("Failures:")
    for test, failure in report.failures:
        print(test)
        print(failure)
        print("--")
    print()
    print("---------------------------")
    print("Ran", report.total(), "tests in", time() - start, "seconds.")
    print(report.passed, "passed")
    print(report.failed, "failed, of which", report.partial, "matched")
    print(report.errors, "broken")
    print(report.skipped, "skipped")
    print()
    print("Applied overrides:", overrides)
    print()
    if report.total() != len(files):
        print("Bouh! Some test were not run", report.total(), "≠", len(files))
