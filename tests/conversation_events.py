import json

from uhlive.stream.conversation.client import S_JOIN_REF

words_decoded = [
    S_JOIN_REF,
    2,
    "conversation:rtxm@test",
    "audio_words_decoded",
    {
        "meta": {
            "model": "generic.lm11.am17.dicGeneric211206.lmwt10",
            "previous_utterance_id": None,
        },
        "value": "bonjour comment ça va",
        "components": [
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
        "country": "fr",
        "start": 1760715687595,
        "speaker": "Alice",
        "client_id": "toto",
        "lang": "fr",
        "conversation": "conversation:rtxm@test",
        "confidence": 1,
        "length": 990,
        "id": "0",
        "campaign_id": "titi",
        "end": 1760715688585,
    },
]

segment_decoded = [
    S_JOIN_REF,
    2,
    "conversation:rtxm@test",
    "audio_segment_decoded",
    {
        "meta": {
            "model": "generic.lm11.am17.dicGeneric211206.lmwt10",
            "previous_utterance_id": None,
        },
        "value": "bonjour comment ça va",
        "components": [
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
        "country": "fr",
        "start": 1760715687595,
        "speaker": "Alice",
        "client_id": "toto",
        "lang": "fr",
        "conversation": "conversation:rtxm@test",
        "confidence": 1,
        "length": 990,
        "id": "0",
        "campaign_id": "titi",
        "end": 1760715688585,
    },
]

speaker_joined = [
    S_JOIN_REF,
    2,
    "conversation:merwan1",
    "speaker_joined",
    {
        "speaker": "robin",
        "interim_results": True,
        "rescoring": True,
        "timestamp": 1613129063523,
    },
]

speaker_left = [
    S_JOIN_REF,
    2,
    "conversation:merwan1",
    "speaker_left",
    {
        "speaker": "robin",
        "timestamp": 1613129073523,
    },
]

entity_number_found = [
    S_JOIN_REF,
    2,
    "conversation:rtxm@test",
    "entity_cardinal_number_recognized",
    {
        "speaker": "Alice",
        "country": "fr",
        "value": 3,
        "start": 9260,
        "length": 200,
        "source": "trois",
        "conversation": "conversation:rtxm@test",
        "campaign_id": "campaignid",
        "confidence": 0.9,
        "display": "3",
        "id": "sd3yeitr-9260",
        "client_id": "rtxm",
        "lang": "fr",
        "end": 9460,
    },
]

entity_location_city_found = [
    S_JOIN_REF,
    2,
    "conversation:rtxm@test",
    "entity_location_city_recognized",
    {
        "id": "Entity.LocationCity-8560",
        "campaign_id": "campaignid",
        "country": "fr",
        "start": 8560,
        "conversation_id": "debug1761295646.4503515",
        "lang": "fr",
        "length": 300,
        "source": "lyon",
        "conversation": "conversation:rtxm@test",
        "meta": {},
        "confidence": 0.99,
        "value": "Lyon",
        "end": 8860,
        "client_id": "rtxm",
        "display": "Lyon",
        "speaker": "Alice",
    },
]


join_successful = json.dumps(
    [
        S_JOIN_REF,
        S_JOIN_REF,
        "conversation:customerid@myconv",
        "phx_reply",
        {"status": "ok", "response": {}},
    ]
)
