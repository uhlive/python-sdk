import json

from uhlive.stream.conversation.client import S_JOIN_REF

words_decoded = [
    S_JOIN_REF,
    2,
    "conversation:merwan1",
    "words_decoded",
    {
        "speaker": "robin",
        "start": 2310,
        "end": 5670,
        "length": 3360,
        "lang": "fr",
        "transcript": "allez-y s' il vous plaît de participer",
        "words": [
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
    },
]

segment_decoded = [
    S_JOIN_REF,
    2,
    "conversation:merwan1",
    "segment_decoded",
    {
        "speaker": "robin",
        "start": 2310,
        "end": 5670,
        "length": 3360,
        "lang": "fr",
        "transcript": "allez-y s' il vous plaît de participer",
        "words": [
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
    "conversation:acme_corp@conference",
    "entity_number_found",
    {
        "annotation": {"canonical": "22", "original": "vingt-deux", "value": 22.0},
        "end": 3690,
        "lang": "fr",
        "length": 960,
        "confidence": 0.9,
        "speaker": "Alice",
        "start": 2730,
    },
]

entity_location_city_found = [
    S_JOIN_REF,
    2,
    "conversation:acme_corp@conference",
    "entity_location_city_found",
    {
        "annotation": {"original": "lyon"},
        "end": 3690,
        "lang": "fr",
        "length": 960,
        "confidence": 0.9,
        "speaker": "Alice",
        "start": 2730,
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
