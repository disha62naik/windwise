"""Builds auditable analytical records for delivery days and summarises them."""
from __future__ import annotations

from datetime import date, time, timedelta
from typing import Any

import pandas as pd

from app.services.accuracy import add_error_columns, compute_metrics
from app.services.forecast_selector import select_forecasts
from app.services.resolution import aggregate_actuals
from app.utils.timestamps import LONDON, decision_cutoff_utc, expected_intervals

OK = "OK"
MISSING_ACTUAL = "MISSING_ACTUAL"
NO_FORECAST = "NO_FORECAST"
MISSING_BOTH = "MISSING_BOTH"


def build_day_records(actuals: pd.DataFrame, forecasts: pd.DataFrame, delivery_day: date,
                      cutoff_local: time, cutoff_days_before: int = 1, minutes: int = 30) -> pd.DataFrame:
    """One row per expected interval of `delivery_day` (London day).

    minutes=30: native half-hours (46/48/50 rows). minutes=60: hourly evaluation, where the
    actual is the mean of the two half-hourly MW values (both required; see resolution.py).
    """
    cutoff = decision_cutoff_utc(delivery_day, cutoff_local, cutoff_days_before)
    expected = expected_intervals(delivery_day, minutes)
    selected = select_forecasts(forecasts, expected, cutoff)
    act = aggregate_actuals(actuals, minutes).drop_duplicates("delivery_start_utc", keep="last")
    df = selected.merge(act, on="delivery_start_utc", how="left")
    df = add_error_columns(df, "selected_forecast_mw", "actual_generation_mw")

    has_f, has_a = df["selected_forecast_mw"].notna(), df["actual_generation_mw"].notna()
    df["data_quality_status"] = MISSING_BOTH
    df.loc[has_f & ~has_a, "data_quality_status"] = MISSING_ACTUAL
    df.loc[~has_f & has_a, "data_quality_status"] = NO_FORECAST
    df.loc[has_f & has_a, "data_quality_status"] = OK
    df["delivery_start_local"] = df["delivery_start_utc"].dt.tz_convert(LONDON)
    df["delivery_date"] = delivery_day.isoformat()
    return df


def build_range_records(actuals: pd.DataFrame, forecasts: pd.DataFrame, start: date, end: date,
                        cutoff_local: time, cutoff_days_before: int = 1, minutes: int = 30) -> pd.DataFrame:
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    frames = [build_day_records(actuals, forecasts, d, cutoff_local, cutoff_days_before, minutes) for d in days]
    return pd.concat(frames, ignore_index=True)


def coverage(records: pd.DataFrame) -> dict[str, int]:
    return {
        "expected_intervals": int(len(records)),
        "actual_intervals": int(records["actual_generation_mw"].notna().sum()),
        "forecast_intervals": int(records["selected_forecast_mw"].notna().sum()),
        "matched_intervals": int((records["data_quality_status"] == OK).sum()),
        "missing_forecast_intervals": int(records["selected_forecast_mw"].isna().sum()),
        "missing_actual_intervals": int(records["actual_generation_mw"].isna().sum()),
        "intervals_with_only_later_forecasts": int((records["selection_status"] == "ONLY_LATER_FORECASTS").sum()),
    }


def summarise(records: pd.DataFrame) -> dict[str, Any]:
    """Overall metrics + coverage + per-delivery-date metrics, all from matched rows only."""
    daily = []
    for day, grp in records.groupby("delivery_date", sort=True):
        m = compute_metrics(grp["selected_forecast_mw"], grp["actual_generation_mw"]).to_dict()
        daily.append({"delivery_date": day, **coverage(grp), **m})
    return {
        "metrics": compute_metrics(records["selected_forecast_mw"], records["actual_generation_mw"]).to_dict(),
        "coverage": coverage(records),
        "daily": daily,
    }


def quality_report(records: pd.DataFrame, actuals_norm, forecasts_norm) -> dict[str, Any]:
    """Coverage plus normalisation findings (invalid/duplicate rows) for the data-quality panel."""
    warnings: list[str] = []
    cov = coverage(records)
    if cov["matched_intervals"] < cov["expected_intervals"]:
        warnings.append(
            f"Only {cov['matched_intervals']} of {cov['expected_intervals']} expected intervals "
            "have both a selected forecast and an actual.")
    for label, norm in (("actual", actuals_norm), ("forecast", forecasts_norm)):
        if norm.invalid:
            warnings.append(f"{len(norm.invalid)} invalid {label} records rejected.")
        if norm.conflicting_duplicates:
            warnings.append(f"{norm.conflicting_duplicates} {label} duplicates had conflicting values.")
    return {
        **cov,
        "invalid_actual_records": len(actuals_norm.invalid),
        "invalid_forecast_records": len(forecasts_norm.invalid),
        "duplicate_actual_records_collapsed": actuals_norm.duplicates_collapsed,
        "duplicate_forecast_records_collapsed": forecasts_norm.duplicates_collapsed,
        "conflicting_forecast_duplicates": forecasts_norm.conflicting_duplicates,
        "non_wind_records_ignored": actuals_norm.ignored_non_wind,
        "warnings": warnings,
    }
