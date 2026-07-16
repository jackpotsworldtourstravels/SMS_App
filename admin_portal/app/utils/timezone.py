from datetime import datetime, timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def to_ist(dt: datetime | None) -> datetime | None:
    """Convert a timestamp to Indian Standard Time for display. Stored
    timestamps stay in UTC — this is a presentation-layer conversion only.
    Naive datetimes (e.g. from SQLite in tests) are assumed to already be
    UTC, matching how every timestamp in this app is generated."""

    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)
