"""Timezone helpers. All instants are tz-aware; naive timestamps are rejected."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

LONDON = ZoneInfo("Europe/London")
INTERVAL = pd.Timedelta(minutes=30)


def to_utc(value: object) -> pd.Timestamp:
    """Parse to a UTC Timestamp. Raises ValueError for naive or unparseable input."""
    try:
        ts = pd.Timestamp(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"unparseable timestamp: {value!r}") from exc
    if ts is pd.NaT:
        raise ValueError("missing timestamp")
    if ts.tzinfo is None:
        raise ValueError(f"naive timestamp not allowed: {value!r}")
    return ts.tz_convert("UTC").as_unit("ns")


def delivery_day_bounds_utc(day: date) -> tuple[pd.Timestamp, pd.Timestamp]:
    """[start, end) of a Europe/London calendar day, expressed in UTC."""
    start = datetime.combine(day, time(0, 0), tzinfo=LONDON)
    end = datetime.combine(day + timedelta(days=1), time(0, 0), tzinfo=LONDON)
    return to_utc(start), to_utc(end)


def expected_intervals(day: date, minutes: int = 30) -> pd.DatetimeIndex:
    """UTC interval starts for a London day. 30-min: 46/48/50 per day; 60-min: 23/24/25."""
    start, end = delivery_day_bounds_utc(day)
    return pd.date_range(start, end, freq=pd.Timedelta(minutes=minutes), inclusive="left", unit="ns")


def decision_cutoff_utc(delivery_day: date, cutoff_local: time, days_before: int = 1) -> pd.Timestamp:
    """Cutoff instant = `cutoff_local` London time on (delivery_day - days_before).

    Ambiguous (clock-back) times resolve to the first occurrence. A cutoff that falls
    in the spring-forward gap does not exist and raises rather than being silently moved.
    """
    local_day = delivery_day - timedelta(days=days_before)
    local = datetime.combine(local_day, cutoff_local, tzinfo=LONDON)
    utc = to_utc(local)
    roundtrip = utc.tz_convert(LONDON)
    if (roundtrip.hour, roundtrip.minute) != (cutoff_local.hour, cutoff_local.minute):
        raise ValueError(f"cutoff {cutoff_local} does not exist on {local_day} (DST gap)")
    return utc


def as_utc_ns(series: pd.Series) -> pd.Series:
    """Coerce a datetime Series to datetime64[ns, UTC] (avoids unit-mismatch on merges)."""
    return pd.to_datetime(series, utc=True).dt.as_unit("ns")
