import os
from urllib.parse import urljoin

from .client import ProtocolError, Recognizer  # noqa
from .events import *  # noqa

SERVER = os.getenv("UHLIVE_API_URL", "wss://api.uh.live")


def build_connection_request(token):
    return urljoin(SERVER, "/bots"), {"Authorization": f"bearer {token}"}
