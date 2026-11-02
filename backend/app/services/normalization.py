"""Raw Elexon records -> validated, UTC-normalised DataFrames.

Units: generation is MW. FUELHH is average MW over the half-hour starting at startTime;
WINDFOR is the forecast MW for the hour starting at startTime (verify against live data).
Missing/invalid generation is rejected and reported, never replaced with zero.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

import pandas as pd

from app.utils.timestamps import LONDON, as_utc_ns, to_utc

ACTUAL_COLUMNS = [
    "delivery_start_utc", "delivery_start_local", "fuel_type",
    "actual_generation_mw", "source_record_identifier",
]
FORECAST_COLUMNS = [
    "delivery_start_utc", "delivery_start_local", "publish_time_utc", "publish_time_local",
    "forecast_generation_mw", "source_record_identifier",
]


@dataclass
class InvalidRecord:
    position: int
    reason: str


@dataclass
class NormalizationResult:
    frame: pd.DataFrame
    invalid: list[InvalidRecord] = field(default_factory=list)
    duplicates_collapsed: int = 0
    conflicting_duplicates: int = 0
    ignored_non_wind: int = 0


def _parse_generation(value: Any) -> float:
    if value is None or isinstance(value, bool):
        raise ValueError("missing generation")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"non-numeric generation: {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError("non-finite generation")
    if number < 0:
        raise ValueError("negative generation")
    return number


def _finish(rows: list[dict], columns: list[str], time_cols: list[str], local_map: dict[str, str]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=columns if not rows else None)
    for col in time_cols:
        frame[col] = as_utc_ns(frame[col]) if rows else pd.to_datetime(pd.Series([], dtype="object"), utc=True).dt.as_unit("ns")
    for utc_col, local_col in local_map.items():
        frame[local_col] = frame[utc_col].dt.tz_convert(LONDON)
    return frame[columns].reset_index(drop=True)


def normalize_actuals(records: Iterable[Mapping[str, Any]]) -> NormalizationResult:
    """FUELHH -> one row per delivery interval; WIND only.

    Duplicate startTime: the record with the latest publishTime wins (ties: last in input).
    """
    result = NormalizationResult(frame=pd.DataFrame())
    kept: dict[pd.Timestamp, tuple[pd.Timestamp, dict]] = {}
    for pos, rec in enumerate(records):
        if str(rec.get("fuelType", "")).upper() != "WIND":
            result.ignored_non_wind += 1
            continue
        try:
            start = to_utc(rec.get("startTime"))
            gen = _parse_generation(rec.get("generation"))
        except ValueError as exc:
            result.invalid.append(InvalidRecord(pos, str(exc)))
            continue
        try:
            published = to_utc(rec["publishTime"]) if rec.get("publishTime") else pd.Timestamp.min.tz_localize("UTC")
        except ValueError:
            published = pd.Timestamp.min.tz_localize("UTC")
        sid = None
        if rec.get("settlementDate") and rec.get("settlementPeriod") is not None:
            sid = f"{rec['settlementDate']}#{rec['settlementPeriod']}"
        row = {"delivery_start_utc": start, "fuel_type": "WIND",
               "actual_generation_mw": gen, "source_record_identifier": sid}
        if start in kept:
            result.duplicates_collapsed += 1
            if published >= kept[start][0]:
                kept[start] = (published, row)
        else:
            kept[start] = (published, row)
    rows = [row for _, row in sorted(kept.values(), key=lambda t: t[1]["delivery_start_utc"])]
    result.frame = _finish(rows, ACTUAL_COLUMNS, ["delivery_start_utc"],
                           {"delivery_start_utc": "delivery_start_local"})
    return result


def normalize_forecasts(records: Iterable[Mapping[str, Any]]) -> NormalizationResult:
    """WINDFOR -> one row per (delivery start, publish time).

    Different publishTimes for one startTime are *revisions* and are all kept. Only an
    identical (startTime, publishTime) key is a duplicate; if its values disagree it is
    counted as conflicting and the last record in input order is kept.
    """
    result = NormalizationResult(frame=pd.DataFrame())
    kept: dict[tuple[pd.Timestamp, pd.Timestamp], dict] = {}
    for pos, rec in enumerate(records):
        try:
            start = to_utc(rec.get("startTime"))
            published = to_utc(rec.get("publishTime"))
            gen = _parse_generation(rec.get("generation"))
        except ValueError as exc:
            result.invalid.append(InvalidRecord(pos, str(exc)))
            continue
        key = (start, published)
        if key in kept:
            result.duplicates_collapsed += 1
            if kept[key]["forecast_generation_mw"] != gen:
                result.conflicting_duplicates += 1
        kept[key] = {
            "delivery_start_utc": start, "publish_time_utc": published,
            "forecast_generation_mw": gen,
            "source_record_identifier": f"{start.isoformat()}|{published.isoformat()}",
        }
    rows = [kept[k] for k in sorted(kept)]
    result.frame = _finish(rows, FORECAST_COLUMNS, ["delivery_start_utc", "publish_time_utc"],
                           {"delivery_start_utc": "delivery_start_local",
                            "publish_time_utc": "publish_time_local"})
    return result
