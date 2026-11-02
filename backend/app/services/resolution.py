"""Common-resolution evaluation: never invents forecast values.

If forecasts are hourly and actuals half-hourly, the ACTUALS are aggregated to the hour
(mean of the two half-hourly MW values, which equals the hourly mean MW for equal-length
intervals). Source data is left unchanged; an hour with only one half-hour is treated as
a missing actual rather than averaged on partial data.

Assumption (verify with scripts/check_elexon.py): startTime marks the START of the interval
in both datasets. UK offsets are whole hours, so UTC hour buckets coincide with London hours.
"""
from __future__ import annotations

import pandas as pd


def detect_forecast_resolution_minutes(forecasts: pd.DataFrame) -> int | None:
    """60 if every forecast startTime is on the hour, 30 if :30 starts also occur, None if no data."""
    if forecasts.empty:
        return None
    minutes = {int(m) for m in forecasts["delivery_start_utc"].dt.minute.unique()}
    if minutes == {0}:
        return 60
    if minutes <= {0, 30}:
        return 30
    raise ValueError(f"unsupported forecast start minutes {sorted(minutes)}; inspect the source data")


def resolve_resolution(setting: str, forecasts: pd.DataFrame) -> int:
    if setting in ("30", "60"):
        return int(setting)
    return detect_forecast_resolution_minutes(forecasts) or 30


def aggregate_actuals(actuals: pd.DataFrame, minutes: int) -> pd.DataFrame:
    cols = ["delivery_start_utc", "actual_generation_mw"]
    if minutes == 30:
        return actuals[cols]
    if minutes != 60:
        raise ValueError("only 30- and 60-minute evaluation is supported")
    if actuals.empty:
        return actuals[cols]
    df = actuals[cols].copy()
    df["bucket"] = df["delivery_start_utc"].dt.floor("h")
    g = df.groupby("bucket")["actual_generation_mw"].agg(["mean", "count"])
    g = g[g["count"] == 2]
    out = g["mean"].rename("actual_generation_mw").reset_index().rename(columns={"bucket": "delivery_start_utc"})
    return out[cols]


def describe(minutes: int) -> dict:
    method = ("native half-hourly: forecast and actual compared per half-hour" if minutes == 30 else
              "hourly: actual = mean of the two half-hourly MW values (both required); forecast used as published, not interpolated")
    return {"minutes": minutes, "method": method}
