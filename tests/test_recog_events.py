from datetime import datetime
from unittest import TestCase

from uhlive.stream.recognition import events

from .recog_events import (
    grammar_defined,
    method_failed,
    params_set,
    recognition_complete,
    recognition_complete_nbests,
    session_opened,
)


class TestEventDeserialization(TestCase):
    def test_session_opened(self):
        event = events.deserialize(session_opened)
        self.assertIsInstance(event, events.Opened)
        self.assertEqual(event.request_id, 0)
        self.assertEqual(event.channel_id, "testuie46e4ui6")
        self.assertEqual(event.headers, {})
        self.assertIsNone(event.completion_cause)
        self.assertIsNone(event.completion_reason)
        self.assertIsNone(event.body)

    def test_grammar_defined(self):
        event = events.deserialize(grammar_defined)
        self.assertIsInstance(event, events.GrammarDefined)
        self.assertEqual(event.request_id, 1)
        self.assertEqual(event.channel_id, "testuie46e4ui6")
        self.assertEqual(event.headers, {})
        self.assertIsNone(event.completion_cause)
        self.assertIsNone(event.completion_reason)
        self.assertIsNone(event.body)

    def test_params_set(self):
        event = events.deserialize(params_set)
        self.assertIsInstance(event, events.ParamsSet)
        self.assertEqual(event.request_id, 2)
        self.assertEqual(event.channel_id, "testuie46e4ui6")
        self.assertEqual(event.headers, {})
        self.assertIsNone(event.completion_cause)
        self.assertIsNone(event.completion_reason)
        self.assertIsNone(event.body)

    def test_recognition_complete(self):
        event = events.deserialize(recognition_complete)
        self.assertIsInstance(event, events.RecognitionComplete)
        self.assertEqual(event.request_id, 3)
        self.assertEqual(event.channel_id, "testuie46e4ui6")
        self.assertEqual(event.headers, {})
        self.assertEqual(event.completion_cause, events.CompletionCause.Success)
        self.assertIsNone(event.completion_reason)
        result = event.body
        self.assertIsInstance(result, events.RecogResult)
        self.assertIsInstance(result.asr, events.Transcript)
        self.assertIsInstance(result.nlu, events.Interpretation)
        self.assertEqual(result.grammar_uri, "session:immat")
        self.assertEqual(result.nlu.value, "bc305fz")
        self.assertEqual(
            result.asr.transcript, "attendez alors voilà baissé trois cent cinq f z"
        )
        self.assertEqual(result.asr.start, datetime(2021, 8, 20, 10, 5, 34, 909000))

    def test_recognition_complete_nbests(self):
        event = events.deserialize(recognition_complete_nbests)
        result = event.body
        self.assertIsInstance(result, events.RecogResult)
        self.assertIsInstance(result.asr, events.Transcript)
        self.assertIsInstance(result.nlu, events.Interpretation)
        self.assertEqual(result.nlu.value, "le137137866cn")
        self.assertEqual(len(result.alternatives), 2)
        best2 = result.alternatives[0]
        self.assertIsInstance(best2, events.RecogResult)
        self.assertIsInstance(best2.asr, events.Transcript)
        self.assertIsInstance(best2.nlu, events.Interpretation)
        self.assertEqual(best2.nlu.value, "le137137866cm")

    def test_method_failed(self):
        event = events.deserialize(method_failed)
        self.assertIsInstance(event, events.MethodFailed)
        self.assertEqual(event.request_id, 2)
        self.assertEqual(event.channel_id, "testuie46e4ui6")
        self.assertEqual(event.headers, {})
        self.assertEqual(event.completion_cause, events.CompletionCause.GramLoadFailure)
        self.assertEqual(event.completion_reason, "unknown grammar 'toto'")

    def test_event_str(self):
        # We just want to be sure we don't raise exceptions
        event = events.deserialize(session_opened)
        print(event)
        event = events.deserialize(grammar_defined)
        print(event)
        event = events.deserialize(params_set)
        print(event)
        event = events.deserialize(recognition_complete)
        print(event)
        event = events.deserialize(method_failed)
        print(event)
