"""
Display helpers.
"""

from datetime import datetime

local_tz = datetime.now().astimezone().tzinfo


def human_datetime(timestamp):
    """Human readable representation of unix timestamp date."""
    utc_dt = datetime.fromtimestamp(timestamp / 1000.0, local_tz)

    return utc_dt.isoformat(sep=" ")
