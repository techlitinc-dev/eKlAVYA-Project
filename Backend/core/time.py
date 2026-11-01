"""
Timestamp and Date Utilities

All timestamps are timezone-aware UTC; dates are local ISO calendar dates.

Author: eKlAVYA Backend
Version: 1.0.0
"""

from datetime import date, datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def today() -> date:
    """Return the current local calendar date."""
    return date.today()


def iso(dt: datetime) -> str:
    """Serialize a datetime to ISO 8601."""
    return dt.isoformat()


def parse_date(value: str) -> date:
    """Parse an ISO 8601 date (YYYY-MM-DD)."""
    return date.fromisoformat(value)
