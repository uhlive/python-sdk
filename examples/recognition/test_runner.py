from pathlib import Path
from time import sleep, time
from typing import Any, Dict, List, Optional, Sequence

import toml  # type: ignore
import websocket as ws  # type: ignore
from basic_sync import AudioStreamer

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
)


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


class TestRunner:
    def __init__(self, fixture_folder: str) -> None:
        self.fixtures = Path(fixture_folder).resolve()
        self.socket: Optional[ws.WebSocket] = None
        self.streamer: Optional[AudioStreamer] = None
        self.client = Recognizer()
        self.codec = "linear"

    def expect(self, *event_classes, ignore=None) -> Event:
        assert self.socket is not None  # to please mypy
        while True:
            event = self.client.receive(self.socket.recv())
            if isinstance(event, event_classes):
                return event
            elif ignore is None or not isinstance(event, ignore):
                raise AssertionError(f"Expected one of {event_classes}, got {event}")

    def check(
        self,
        audio_file: Path,
        grammars: Sequence[str],
        params: Dict[str, Any],
        expected: Expectation,
    ) -> None:
        """Raise an exception if the test fails."""
        assert self.socket is not None  # to please mypy
        assert self.streamer is not None  # to please mypy
        ext = audio_file.suffix[1:]
        if ext == "pcm":
            ext = "linear"
        if ext != self.codec:
            self.streamer.suspend()
            self.codec = ext
            self.socket.send(self.client.close())
            self.expect(Closed)
            self.socket.send(self.client.open("testsuite", audio_codec=self.codec))
            self.expect(Opened)
            self.streamer.resume()
        self.streamer.play(audio_file, codec=self.codec)
        self.socket.send(self.client.recognize(*grammars, **params))
        # TODO: we may want to test StartOfInput accuracy
        try:
            self.expect(RecognitionInProgress)
            if (
                params["recognition_mode"] == "normal"
                and expected.completion_cause != CompletionCause.NoInputTimeout
            ):
                self.expect(StartOfInput)
            event = self.expect(RecognitionComplete)
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
            self.streamer.skip()

    def walk_tests(self, in_files: Sequence[str], overrides: Dict[str, Any]):
        files: List[Path]
        if not in_files:
            files = list(self.fixtures.glob("*.test"))
            honor_skipped = True
        else:
            files = [self.fixtures / path for path in in_files]
            honor_skipped = False
        nb_tests = len(files)
        passed = 0
        failed = 0
        errors = 0
        skipped = 0
        failures = []
        start = time()
        for i, test_conf in enumerate(files, 1):
            print(
                f"{i}/{nb_tests} —", "Processing", test_conf.name, end="… ", flush=True
            )
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
                self.check(
                    self.fixtures / test["audio"],
                    test["grammars"],
                    test["params"],
                    expected,
                )
            except RecognitionFailed as e:
                print("\033[91m failed\033[0m")
                failures.append((test_conf, e))
                failed += 1
            except Exception as e:
                print("\033[93m error\033[0m")
                print("unable to run test:", e)
                errors += 1
            else:
                passed += 1
                print("\033[92m passed\033[0m")
            sleep(0.8)
        print("=============")
        print()
        print("Ran", nb_tests, "tests in", time() - start, "seconds.")
        print(passed, "passed")
        print(failed, "failed")
        print(errors, "broken")
        print(skipped, "skipped")
        print()
        print("Applied overrides:", overrides)
        print()
        print("Failures:")
        for test, failure in failures:
            print(test)
            print(failure)
            print("--")

    def run(
        self,
        uhlive_url: str,
        uhlive_token: str,
        files: Sequence[str],
        overrides: Dict[str, Any],
    ):
        self.socket = socket = ws.create_connection(
            uhlive_url, header={"Authorization": f"bearer {uhlive_token}"}
        )
        try:
            self.socket = socket
            self.streamer = AudioStreamer(socket, self.client, verbose=False)
            socket.send(self.client.open("testsuite"))
            self.expect(Opened)
            self.streamer.start()  # type: ignore
            try:
                self.walk_tests(files, overrides)
            finally:
                self.streamer.skip()  # type: ignore
                self.streamer.stop()  # type: ignore
                socket.send(self.client.close())
                self.expect(Closed)
        finally:
            socket.close()


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
    parser.add_argument("--overrides", nargs="*", help="parameters to override")
    args = parser.parse_args()
    runner = TestRunner(args.test_folder)
    uhlive_url = os.environ["UHLIVE_API_URL"]
    uhlive_token = os.environ["UHLIVE_API_TOKEN"]
    overrides = {}
    for override in args.overrides or []:
        param, value = override.split("=")
        if value.isdigit():
            value = int(value)
        overrides[param] = value
    runner.run(uhlive_url, uhlive_token, args.tests, overrides)
