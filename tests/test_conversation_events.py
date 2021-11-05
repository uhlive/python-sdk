from unittest import TestCase

from uhlive.stream.conversation.events import (
    EntityFound,
    Event,
    SegmentDecoded,
    SpeakerJoined,
    SpeakerLeft,
    WordsDecoded,
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

        self.assertEqual(event.speaker, "robin")

        message = speaker_left
        event = Event.from_message(message)

        self.assertEqual(event.speaker, "robin")

    def test_transcript(self):
        message = words_decoded
        event = Event.from_message(message)

        self.assertEqual(event.transcript, "allez-y s' il vous plaît de participer")

    def test_timestamps(self):
        event = Event.from_message(words_decoded)
        self.assertEqual(event.start, 2310)
        self.assertEqual(event.end, 5670)
        self.assertEqual(event.length, 3360)
        event = Event.from_message(entity_number_found)
        self.assertEqual(event.start, 2730)
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
        self.assertIsInstance(event, WordsDecoded)

        event = Event.from_message(segment_decoded)
        self.assertIsInstance(event, SegmentDecoded)

        message = speaker_left
        event = Event.from_message(message)
        self.assertIsInstance(event, SpeakerLeft)

        event = Event.from_message(entity_number_found)
        self.assertIsInstance(event, EntityFound)
        self.assertEqual(event.entity_name, "number")

    def test_annotation(self):
        annotation = Event.from_message(entity_number_found)
        self.assertEqual(annotation.canonical, "22")
        self.assertEqual(annotation.value, 22.0)
        self.assertEqual(annotation.original, "vingt-deux")

    def test_words(self):
        message = words_decoded
        event = Event.from_message(message)

        self.assertEqual(
            event.words,
            [
                {
                    "confidence": 0.94202,
                    "start": 960,
                    "end": 1320,
                    "length": 360,
                    "word": "allez-y",
                },
                {
                    "confidence": 0.954795,
                    "start": 1320,
                    "end": 1350,
                    "length": 30,
                    "word": "s'",
                },
                {
                    "confidence": 0.999226,
                    "start": 1350,
                    "end": 1440,
                    "length": 90,
                    "word": "il",
                },
                {
                    "confidence": 0.999994,
                    "start": 1440,
                    "end": 1560,
                    "length": 120,
                    "word": "vous",
                },
                {
                    "confidence": 0.99975,
                    "start": 1560,
                    "end": 1740,
                    "length": 180,
                    "word": "plaît",
                },
                {
                    "confidence": 0.663816,
                    "start": 1740,
                    "end": 1770,
                    "length": 30,
                    "word": "de",
                },
                {
                    "confidence": 0.852544,
                    "start": 1770,
                    "end": 2700,
                    "length": 930,
                    "word": "participer",
                },
            ],
        )

        first = event.words[0]
        for attr in ["start", "end", "length", "word", "confidence"]:
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
        self.assertIsInstance(event, EntityFound)
        self.assertEqual(event.entity_name, "location_city")
        self.assertEqual(event.original, "lyon")
        self.assertEqual(event.confidence, 0.9)
