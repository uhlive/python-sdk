from unittest import TestCase

from uhlive.stream.conversation import Conversation, Ok, ProtocolError

from .conversation_events import join_successful


class TestConnection(TestCase):
    def test_join(self):
        client = Conversation("customerid", "myconv", "john_test")
        frame = client.join(model="en", country="us")
        self.assertEqual(
            frame,
            r'["1","1","conversation:customerid@myconv","phx_join",{"readonly":false,"speaker":"john_test","model":"en","country":"us","interim_results":true,"rescoring":true,"origin":0,"audio_codec":"linear"}]',
        )
        with self.assertRaises(ProtocolError):
            client.send_audio_chunk(bytes(60))

        with self.assertRaises(ProtocolError):
            client.leave()

    def test_joined(self):
        client = Conversation("customerid", "myconv", "john_test")
        client.join()
        event = client.receive(join_successful)
        self.assertIsInstance(event, Ok)

        # Can't join twice
        with self.assertRaises(ProtocolError):
            client.join()

        # Can stream
        client.send_audio_chunk(bytes(60))
        # Can leave
        client.leave()

    def test_leave(self):
        client = Conversation("customerid", "myconv", "john_test")
        client.join()
        client.receive(join_successful)

        frame = client.leave()
        self.assertEqual(
            frame, r'["1","2","conversation:customerid@myconv","phx_leave",{}]'
        )

    def receive_wrong_topic(self):
        client = Conversation("customerid", "unrelated_topic", "john_test")
        with self.assertRaises(AssertionError):
            client.receive(join_successful)
