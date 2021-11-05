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
