"""
Authentication helpers
"""

import os
from typing import Dict, Tuple

SERVER = os.getenv("UHLIVE_AUTH_SERVER", "id.uh.live")
REALM = os.getenv("UHLIVE_AUTH_REALM", "uhlive")


def build_authentication_request(
    client_id: str, client_secret: str, user_id: str = "", user_pwd: str = ""
) -> Tuple[str, Dict[str, str]]:
    """Build a couple (url, param dict) to be use in an HTTP POST request to get the API access_token.

    Synchronous example using ``requests``:

    ```python
    auth_url, auth_params = build_authentication_request(uhlive_client, uhlive_secret)
    login = requests.post(auth_url, data=auth_params)
    login.raise_for_status()
    uhlive_token = login.json()["access_token"]
    ```
    """

    url = f"https://{SERVER}/realms/{REALM}/protocol/openid-connect/token"
    data = {
        "client_id": client_id,
        "grant_type": "client_credentials" if not user_id else "password",
        "client_secret": client_secret,
    }
    if user_id:
        data["username"] = user_id
        data["password"] = user_pwd
    return url, data
