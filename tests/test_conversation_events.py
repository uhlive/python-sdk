from unittest import TestCase

from uhlive.stream.conversation.events import (
    AudioSegmentDecoded,
    AudioWordsDecoded,
    EntityRecognized,
    Event,
    SpeakerJoined,
    SpeakerLeft,
)

from .conversation_events import (
    entity_location_city_found,
    entity_number_found,
    segment_decoded,
    speaker_joined,
    speaker_left,
    words_decoded,
)


class TestConversationEventReceived(TestCase):
    def test_creation(self):
        message = words_decoded
        Event.from_message(message)

    def test_speaker(self):
        message = words_decoded
        event = Event.from_message(message)

        self.assertEqual(event.speaker, "Alice")

        message = speaker_left
        event = Event.from_message(message)

        self.assertEqual(event.speaker, "robin")

    def test_transcript(self):
        message = words_decoded
        event = Event.from_message(message)

        self.assertEqual(event.value, "bonjour comment ça va")

    def test_timestamps(self):
        event = Event.from_message(words_decoded)
        self.assertEqual(event.start, 1760715687595)
        self.assertEqual(event.end, 1760715688585)
        self.assertEqual(event.length, 990)
        event = Event.from_message(entity_number_found)
        self.assertEqual(event.start, 9260)
        event = Event.from_message(speaker_left)
        self.assertEqual(event.timestamp, 1613129073523)

    def test_lang(self):
        event = Event.from_message(words_decoded)
        self.assertEqual(event.lang, "fr")
        event = Event.from_message(entity_number_found)
        self.assertEqual(event.lang, "fr")

    def test_type(self):
        message = words_decoded
        event = Event.from_message(message)
        self.assertIsInstance(event, AudioWordsDecoded)

        event = Event.from_message(segment_decoded)
        self.assertIsInstance(event, AudioSegmentDecoded)

        message = speaker_left
        event = Event.from_message(message)
        self.assertIsInstance(event, SpeakerLeft)

        event = Event.from_message(entity_number_found)
        self.assertIsInstance(event, EntityRecognized)
        self.assertEqual(event.entity_name, "cardinal_number")

    def test_annotation(self):
        annotation = Event.from_message(entity_number_found)
        self.assertEqual(annotation.display, "3")
        self.assertEqual(annotation.value, 3)
        self.assertEqual(annotation.source, "trois")

    def test_words(self):
        message = words_decoded
        event = Event.from_message(message)

        self.assertEqual(
            event.components,
            [
                {
                    "confidence": 1,
                    "end": 1760715687925,
                    "length": 330,
                    "start": 1760715687595,
                    "value": "bonjour",
                },
                {
                    "end": 1760715688135,
                    "length": 210,
                    "start": 1760715687925,
                    "value": "comment",
                    "confidence": 1,
                },
                {
                    "start": 1760715688135,
                    "value": "ça",
                    "confidence": 1,
                    "end": 1760715688285,
                    "length": 150,
                },
                {
                    "confidence": 1,
                    "end": 1760715688585,
                    "length": 300,
                    "start": 1760715688285,
                    "value": "va",
                },
            ],
        )

        first = event.components[0]
        for attr in ["start", "end", "length", "value", "confidence"]:
            self.assertEqual(getattr(first, attr), first[attr])

    def test_speaker_joined(self):
        event = Event.from_message(speaker_joined)
        self.assertIsInstance(event, SpeakerJoined)
        self.assertEqual(event.speaker, "robin")
        self.assertTrue(event.rescoring)
        self.assertTrue(event.interim_results)
        self.assertEqual(event.timestamp, 1613129063523)

    def test_instantiate_ner_event(self):
        event = Event.from_message(entity_location_city_found)
        self.assertIsInstance(event, EntityRecognized)
        self.assertEqual(event.entity_name, "location_city")
        self.assertEqual(event.source, "lyon")
        self.assertEqual(event.confidence, 0.99)
