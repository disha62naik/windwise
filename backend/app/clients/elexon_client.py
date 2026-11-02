"""Elexon Insights API client (no API key required).

Endpoints/params below come from the Elexon OpenAPI spec as reported by several
independent projects; they were NOT verified live from this build environment.
Run `python -m scripts.check_elexon` (TODO) from a networked machine to confirm.

  FUELHH/stream : settlementDateFrom, settlementDateTo (yyyy-MM-dd), fuelType=WIND
  WINDFOR/stream: publishDateTimeFrom, publishDateTimeTo (ISO date-time, inclusive)
Stream endpoints return a plain JSON array and are not paginated, so large ranges are
chunked client-side.
"""
from __future__ import annotations

import logging
import time as _time
from datetime import date, timedelta
from typing import Any, Callable

import httpx
import pandas as pd

from app.config import Settings

log = logging.getLogger("windwise.elexon")
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class ElexonError(Exception):
    """Controlled upstream failure; message is safe to show to users."""


class ElexonResponseError(ElexonError):
    """Upstream returned something that is not the expected record array."""


class ElexonClient:
    def __init__(self, settings: Settings | None = None, client: httpx.Client | None = None,
                 sleep: Callable[[float], None] = _time.sleep) -> None:
        self.settings = settings or Settings.from_env()
        timeout = httpx.Timeout(self.settings.read_timeout_s, connect=self.settings.connect_timeout_s)
        self._client = client or httpx.Client(base_url=self.settings.elexon_base_url, timeout=timeout)
        self._sleep = sleep

    def _get_records(self, path: str, params: dict[str, Any]) -> list[dict]:
        last: Exception | None = None
        for attempt in range(self.settings.max_retries + 1):
            try:
                resp = self._client.get(path, params=params)
                if resp.status_code in RETRYABLE_STATUS:
                    raise httpx.HTTPStatusError("transient", request=resp.request, response=resp)
                if resp.status_code >= 400:  # permanent client error: do not retry
                    raise ElexonError(f"Elexon rejected the request ({resp.status_code}) for {path}")
                return self._validate(resp)
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last = exc
                delay = min(self.settings.backoff_base_s * 2 ** attempt, self.settings.backoff_max_s)
                log.warning("transient Elexon failure on %s (attempt %d): %s", path, attempt + 1, type(exc).__name__)
                if attempt < self.settings.max_retries:
                    self._sleep(delay)
        raise ElexonError(f"Elexon unavailable after {self.settings.max_retries + 1} attempts") from last

    @staticmethod
    def _validate(resp: httpx.Response) -> list[dict]:
        try:
            body = resp.json()
        except ValueError as exc:
            raise ElexonResponseError("Elexon returned non-JSON content") from exc
        if isinstance(body, dict) and isinstance(body.get("data"), list):
            body = body["data"]
        if not isinstance(body, list) or not all(isinstance(r, dict) for r in body):
            raise ElexonResponseError("Elexon response was not a list of records")
        return body

    def fetch_actuals(self, start: date, end: date) -> list[dict]:
        """WIND actuals for settlement dates start..end inclusive (range chunked to 14 days)."""
        out: list[dict] = []
        cur = start
        while cur <= end:
            chunk_end = min(cur + timedelta(days=13), end)
            out += self._get_records("/datasets/FUELHH/stream", {
                "settlementDateFrom": cur.isoformat(), "settlementDateTo": chunk_end.isoformat(),
                "fuelType": "WIND"})
            cur = chunk_end + timedelta(days=1)
        return out

    def fetch_forecasts(self, publish_from: pd.Timestamp, publish_to: pd.Timestamp) -> list[dict]:
        """All WINDFOR revisions with publishTime in [publish_from, publish_to] (chunked)."""
        out: list[dict] = []
        step = pd.Timedelta(days=self.settings.forecast_chunk_days)
        cur = publish_from
        while cur <= publish_to:
            chunk_end = min(cur + step - pd.Timedelta(seconds=1), publish_to)
            out += self._get_records("/datasets/WINDFOR/stream", {
                "publishDateTimeFrom": cur.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "publishDateTimeTo": chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ")})
            cur = chunk_end + pd.Timedelta(seconds=1)
        return out
