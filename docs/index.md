# Welcome to the Uh!ive Python SDK

The Uh!ive Python SDK is a library to access our live Automated Speech Recognition online APIs.
It provides [I/O Free](https://sans-io.readthedocs.io/index.html) Python abstractions over the underlying protocols and workflows to hide the complexity.

By providing an I/O Free implementation, we let developers choose whatever websocket transport library and paradigm — synchronous or asynchronous (asyncio) — they like most.

## Access to the API

In order to have access to our online APIs, your company needs to register for an account. Depending on the plan, you may get two kinds of credentials:

* Either a `client_id` and `client_secret`;
* or a `client_id`, `user_id` and `user_password`.

In all cases, those credentials are used to retrieve a one time access token from our SSO.

You are free to use whatever HTTP client library you like.

Here is a synchronous example using `requests`:

```python
from uhlive.auth import build_authentication_request
import requests

uhlive_client = "…"
uhlive_secret = "…"
# user_id = "…"
# user_password = "…"

auth_url, auth_params = build_authentication_request(uhlive_client, uhlive_secret)
# or auth_url, auth_params = build_authentication_request(uhlive_client, user_id=user_id, user_pwd=user_password)
login = requests.post(auth_url, data=auth_params)
login.raise_for_status()
uhlive_token = login.json()["access_token"]
```

Here is an asynchronous example using `aiohttp`:

```python
import asyncio
from uhlive.auth import build_authentication_request
from aiohttp import ClientSession

uhlive_client = "…"
uhlive_secret = "…"
# user_id = "…"
# user_password = "…"


async def main(uhlive_client, uhlive_secret):
    async with ClientSession() as session:
        auth_url, auth_params = build_authentication_request(
            uhlive_client, uhlive_secret
        )
        async with session.post(auth_url, data=auth_params) as login:
            login.raise_for_status()
            body = await login.json()
            uhlive_token = body["access_token"]
        # continue with Stream API of your choice
        # ...

asyncio.run(main(uhlive_client, uhlive_secret))
```

Then this one time token allows you to connect to any subscribed API within 5 minutes.

* [Auth API reference](auth.md)


## Conversation API to analyze human to human interactions.

Also known as the human to human (H2H) stream API.

* [High level overview](https://docs.allo-media.net/stream-h2h/overview/#high-level-overview-and-concepts)
* [Python SDK API documentation](conversation_api.md)

## Recognition and interpretation API for voice bots.

Also known as the human to bot (H2B) stream API.

* [High level overview](https://docs.allo-media.net/stream-h2b/#real-time-stream-api-for-voicebots)
* [Python SDK API documentation](recognition_api.md)


## Changelog

### v1.5.0

* Support for the `n_best_list_length` parameter to get alternatives transcriptions and interpretations
  when available.

### v1.4.0

* Support for the `session_id` parameter to the `open` command.

### v1.3.1

Full API documentation.

### v1.3.0

* Support for `SegmentNormalized`
* SSO
* Concurrent test runner `test_runner_async.py` in `examples/recognition`

### v1.2.0

* Improved streamer
* Improved test_runner.py
* Forbid sharing connection between conversations

### v1.1.0

* Support for passing codec parameter
