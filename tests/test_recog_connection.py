from unittest import TestCase

from uhlive.stream.recognition import Opened, ProtocolError, Recognizer

from .recog_events import recognition_complete, recognition_in_progress, session_opened


class TestConnection(TestCase):
    def test_open(self):
        client = Recognizer()
        frame = client.open("mycustomer", "mychan")
        self.assertEqual(
            frame,
            r'{"command":"OPEN","request_id":1,"channel_id":"mychan","headers":{"custom_id":"mycustomer","audio_codec":"linear","session_id":""},"body":""}',
        )
        with self.assertRaises(ProtocolError):
            client.get_params()
        with self.assertRaises(ProtocolError):
            client.send_audio_chunk(b"trntrntrntnrtsrn")

    def test_opened(self):
        client = Recognizer()
        event = client.receive(session_opened)
        self.assertIsInstance(event, Opened)
        frame = client.get_params()
        self.assertEqual(
            frame,
            r'{"command":"GET-PARAMS","request_id":1,"channel_id":"testuie46e4ui6","headers":{},"body":""}',
        )
        # Can't open twice
        with self.assertRaises(ProtocolError):
            client.open("test", "test")

        # we can stream
        client.send_audio_chunk(b"trntrntrntnrtsrn")

    def test_recognize(self):
        client = Recognizer()
        client.receive(session_opened)
        frame = client.define_grammar(
            "speech/spelling/mixed?regex=[a-z]{2}[0-9]{9}[a-z]{2}", "parcel_num"
        )
        self.assertEqual(
            frame,
            r'{"command":"DEFINE-GRAMMAR","request_id":1,"channel_id":"testuie46e4ui6","headers":{"content_id":"parcel_num","content_type":"text/uri-list"},"body":"builtin:speech/spelling/mixed?regex=[a-z]{2}[0-9]{9}[a-z]{2}"}',
        )
        frame = client.recognize("session:parcel_num", no_input_timeout=5000)
        self.assertEqual(
            frame,
            r'{"command":"RECOGNIZE","request_id":2,"channel_id":"testuie46e4ui6","headers":{"recognition_mode":"normal","content_type":"text/uri-list","start_input_timers":true,"no_input_timeout":5000},"body":"session:parcel_num"}',
        )

    def test_recognition_in_progress(self):
        client = Recognizer()
        client.receive(session_opened)
        client.receive(recognition_in_progress)
        # Can't have multiple recognition processes
        with self.assertRaises(ProtocolError):
            client.recognize("builtin:speech/transcribe")

        # Only stop and start-input-timers are valid
        with self.assertRaises(ProtocolError):
            client.get_params()

        self.assertEqual(
            client.start_input_timers(),
            r'{"command":"START-INPUT-TIMERS","request_id":1,"channel_id":"testuie46e4ui6","headers":{},"body":""}',
        )

        self.assertEqual(
            client.stop(),
            r'{"command":"STOP","request_id":2,"channel_id":"testuie46e4ui6","headers":{},"body":""}',
        )

        # we can stream too
        client.send_audio_chunk(b"trntrntrntnrtsrn")

    def test_set_params(self):
        client = Recognizer()
        client.receive(session_opened)
        self.assertEqual(
            client.set_params(speech_language="fr", confidence_threshold=0.7),
            r'{"command":"SET-PARAMS","request_id":1,"channel_id":"testuie46e4ui6","headers":{"speech_language":"fr","confidence_threshold":0.7},"body":""}',
        )

    def test_recognition_complete(self):
        client = Recognizer()
        client.receive(session_opened)
        client.receive(recognition_in_progress)
        with self.assertRaises(ProtocolError):
            client.recognize("builtin:speech/transcribe")
        client.receive(recognition_complete)
        # Now we can start another recognition process
        client.recognize("builtin:speech/transcribe")
