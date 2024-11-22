grammar_defined = r"""
{
    "event": "GRAMMAR-DEFINED",
    "request_id": 1,
    "channel_id": "testuie46e4ui6",
    "headers":
    {},
    "completion_cause": null,
    "completion_reason": null,
    "body": null
}
"""


session_opened = r"""
{
  "event": "OPENED",
  "request_id": 0,
  "channel_id": "testuie46e4ui6",
  "completion_cause": null,
  "completion_reason": null,
  "headers": {},
  "body": ""
}
"""

params_set = r"""
{
  "event": "PARAMS-SET",
  "request_id": 2,
  "channel_id": "testuie46e4ui6",
  "completion_cause": null,
  "completion_reason": null,
  "headers": {},
  "body": ""
}
"""

recognition_complete = r"""
{
  "event": "RECOGNITION-COMPLETE",
  "request_id": 3,
  "channel_id": "testuie46e4ui6",
  "completion_cause": "Success",
  "completion_reason": null,
  "headers": {},
  "body": {
    "asr": {
          "transcript": "attendez alors voilà baissé trois cent cinq f z",
          "confidence": 0.9,
          "start": 1629453934909,
          "end": 1629453944833
      },
    "nlu": {
          "type": "builin:speech/spelling/mixed",
          "value": "bc305fz",
          "confidence": 0.86
      },
    "grammar_uri": "session:immat"
  }
}
"""

method_failed = r"""
{
  "event": "METHOD-FAILED",
  "request_id": 2,
  "channel_id": "testuie46e4ui6",
  "completion_cause": "GramLoadFailure",
  "completion_reason": "unknown grammar 'toto'",
  "headers": {},
  "body": ""
}
"""

recognition_in_progress = r"""
{
  "event": "RECOGNITION-IN-PROGRESS",
  "request_id": 3,
  "channel_id": "testuie46e4ui6",
  "completion_cause": "Success",
  "completion_reason": null,
  "headers": {},
  "body": ""
}
"""

recognition_complete_nbests = r"""
{
    "event": "RECOGNITION-COMPLETE",
    "request_id": 5,
    "channel_id": "6276ee5ec29e4",
    "headers":
    {},
    "completion_cause": "Success",
    "completion_reason": "success",
    "body":
    {
        "asr":
        {
            "transcript": "l e cent trente-sept cent trente-sept huit cent soixante-six c n",
            "confidence": 0.966104,
            "start": 1732207126566,
            "end": 1732207132536
        },
        "nlu":
        {
            "type": "builtin:speech/spelling/mixed",
            "value": "le137137866cn",
            "confidence": 0.9467347
        },
        "grammar_uri": "session:parcel",
        "asr_model": "fr.epellation.v26",
        "version": "1.38.0",
        "alternatives":
        [
            {
                "asr":
                {
                    "transcript": "l e cent trente-sept cent trente-sept huit cent soixante-six c m",
                    "confidence": 0.939056,
                    "start": 1732207126566,
                    "end": 1732207132536
                },
                "nlu":
                {
                    "type": "builtin:speech/spelling/mixed",
                    "value": "le137137866cm",
                    "confidence": 0.90423137
                },
                "grammar_uri": "session:parcel",
                "asr_model": "fr.epellation.v26",
                "version": "1.38.0"
            },
            {
                "asr":
                {
                    "transcript": "e l e cent trente-sept cent trente-sept huit cent soixante-six c n",
                    "confidence": 0.886761,
                    "start": 1732207123716,
                    "end": 1732207132536
                },
                "nlu":
                {
                    "type": "builtin:speech/spelling/mixed",
                    "value": "le137137866cn",
                    "confidence": 0.8301418
                },
                "grammar_uri": "session:parcel",
                "asr_model": "fr.epellation.v26",
                "version": "1.38.0"
            }
        ]
    }
}
"""
