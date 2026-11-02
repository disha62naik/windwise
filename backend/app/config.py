"""Runtime configuration, read from environment variables (see .env.example)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import time


def _parse_hhmm(value: str) -> time:
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


@dataclass(frozen=True)
class Settings:
    elexon_base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"
    connect_timeout_s: float = 10.0
    read_timeout_s: float = 60.0
    max_retries: int = 3
    backoff_base_s: float = 1.0
    backoff_max_s: float = 8.0
    # Decision cutoff: ASSUMPTION (not stated in the brief). Local London clock time,
    # `cutoff_days_before` days before the delivery date. Fully configurable.
    cutoff_local_time: time = time(9, 20)
    cutoff_days_before: int = 1
    # Forecasts are fetched by *publication* time. This is how far before the first
    # cutoff we start, so December 2025 publications for early-January delivery are kept.
    forecast_lookback_days: int = 7
    forecast_chunk_days: int = 7
    max_range_days: int = 62
    cache_ttl_s: float = 900.0
    # Only Europe/London is supported: the market day, cutoff and DST logic are defined in it.
    timezone: str = "Europe/London"
    # "auto" detects the forecast resolution from the data; "30" / "60" force it.
    evaluation_resolution: str = "auto"
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ.get
        tz = env("TIMEZONE", cls.timezone)
        if tz != "Europe/London":
            raise ValueError("TIMEZONE: only Europe/London is supported")
        res = env("EVALUATION_RESOLUTION", cls.evaluation_resolution)
        if res not in ("auto", "30", "60"):
            raise ValueError("EVALUATION_RESOLUTION must be auto, 30 or 60")
        return cls(
            evaluation_resolution=res,
            elexon_base_url=env("ELEXON_BASE_URL", cls.elexon_base_url),
            connect_timeout_s=float(env("ELEXON_CONNECT_TIMEOUT_S", cls.connect_timeout_s)),
            read_timeout_s=float(env("ELEXON_READ_TIMEOUT_S", cls.read_timeout_s)),
            max_retries=int(env("ELEXON_MAX_RETRIES", cls.max_retries)),
            cutoff_local_time=_parse_hhmm(env("DECISION_CUTOFF_LOCAL_TIME", "09:20")),
            cutoff_days_before=int(env("DECISION_CUTOFF_DAYS_BEFORE", cls.cutoff_days_before)),
            forecast_lookback_days=int(env("FORECAST_LOOKBACK_DAYS", cls.forecast_lookback_days)),
            cache_ttl_s=float(env("CACHE_TTL_S", cls.cache_ttl_s)),
            cors_origins=tuple(
                o.strip() for o in env("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
            ),
        )
