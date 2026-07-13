from datetime import datetime, timezone
from typing import Optional

from dateutil import parser as dateparser


def parse_time(raw: str) -> Optional[datetime]:
    """Parse any time string to UTC datetime."""
    try:
        dt = dateparser.parse(raw)
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None
