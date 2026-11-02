"""Fetch + normalise source data for a range of delivery dates, with a small TTL cache."""
from __future__ import annotations

import calendar
import time as _time
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

from app.clients.elexon_client import ElexonClient
from app.config import Settings
from app.services.normalization import NormalizationResult, normalize_actuals, normalize_forecasts
from app.utils.timestamps import decision_cutoff_utc, delivery_day_bounds_utc


@dataclass
class LoadedData:
    actuals: NormalizationResult
    forecasts: NormalizationResult
    publish_from: pd.Timestamp
    publish_to: pd.Timestamp
    fetched_at: pd.Timestamp
    includes_post_cutoff_revisions: bool = False


def forecast_publish_window(start: date, end: date, s: Settings,
                            include_later: bool = False) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Publish-time window needed for delivery dates start..end.

    Starts `forecast_lookback_days` before the FIRST cutoff, so December publications
    for early-January delivery are included. By default it ends at the LAST cutoff, so
    nothing published after a decision cutoff is downloaded for analysis. `include_later`
    extends to the end of the delivery period; used ONLY by the revision-audit view to show
    revisions that were unavailable at the cutoff (the selector still never uses them).
    """
    first = decision_cutoff_utc(start, s.cutoff_local_time, s.cutoff_days_before)
    last = decision_cutoff_utc(end, s.cutoff_local_time, s.cutoff_days_before)
    if include_later:
        last = delivery_day_bounds_utc(end)[1]
    return first - pd.Timedelta(days=s.forecast_lookback_days), last


def load_range(client: ElexonClient, start: date, end: date, s: Settings,
               include_later: bool = False) -> LoadedData:
    if end < start:
        raise ValueError("end before start")
    if (end - start).days + 1 > s.max_range_days:
        raise ValueError(f"range exceeds {s.max_range_days} days")
    p_from, p_to = forecast_publish_window(start, end, s, include_later)
    actuals = normalize_actuals(client.fetch_actuals(start - timedelta(days=1), end + timedelta(days=1)))
    forecasts = normalize_forecasts(client.fetch_forecasts(p_from, p_to))
    return LoadedData(actuals, forecasts, p_from, p_to, pd.Timestamp.now(tz="UTC"), include_later)


def month_bounds(day: date) -> tuple[date, date]:
    return day.replace(day=1), day.replace(day=calendar.monthrange(day.year, day.month)[1])


class DataService:
    """Caches normalised source data (raw revisions retained) per range; metrics are not cached."""

    MAX_ENTRIES = 8

    def __init__(self, client: ElexonClient, settings: Settings) -> None:
        self.client, self.settings = client, settings
        self._cache: dict[tuple, tuple[float, LoadedData]] = {}

    def get_range(self, start: date, end: date, include_later: bool = False) -> LoadedData:
        # Requests inside one calendar month share a single month-sized load.
        if start.replace(day=1) == end.replace(day=1):
            start, end = month_bounds(start)
        key = (start, end, include_later)
        hit = self._cache.get(key)
        if hit and _time.monotonic() - hit[0] < self.settings.cache_ttl_s:
            return hit[1]
        data = load_range(self.client, start, end, self.settings, include_later)
        if len(self._cache) >= self.MAX_ENTRIES:
            self._cache.pop(min(self._cache, key=lambda k: self._cache[k][0]))
        self._cache[key] = (_time.monotonic(), data)
        return data
