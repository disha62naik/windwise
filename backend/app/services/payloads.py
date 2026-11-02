"""Pure functions turning loaded data into JSON-ready API payloads (no web framework)."""
from __future__ import annotations

from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from app.config import Settings
from app.services.analysis import (OK, build_day_records, build_range_records, coverage,
                                   quality_report, summarise)
from app.services.data_loader import LoadedData
from app.services.forecast_selector import revision_history
from app.services.resolution import describe, resolve_resolution
from app.utils.timestamps import LONDON, decision_cutoff_utc

UNITS = {"generation": "MW", "error": "MW", "error_convention": "forecast - actual (positive = over-forecast)"}
TZ = "Europe/London"


def _f(x: Any) -> float | None:
    return None if x is None or pd.isna(x) else float(x)


def _ts(x: Any) -> str | None:
    return None if x is None or pd.isna(x) else pd.Timestamp(x).isoformat()


def status_of(cov: dict) -> str:
    """empty: nothing matched. partial: forecasts or actuals exist that could not be paired
    (or actuals are missing). ok otherwise. Hourly-forecast gaps alone do not make it partial."""
    if cov["matched_intervals"] == 0:
        return "empty"
    if cov["missing_actual_intervals"] > 0 or cov["matched_intervals"] < cov["forecast_intervals"]:
        return "partial"
    return "ok"


def records_json(rec: pd.DataFrame) -> list[dict]:
    out = []
    for r in rec.to_dict("records"):
        out.append({
            "delivery_start_utc": _ts(r["delivery_start_utc"]),
            "delivery_start_local": _ts(r["delivery_start_local"]),
            "delivery_date": r["delivery_date"],
            "forecast_mw": _f(r["selected_forecast_mw"]),
            "actual_mw": _f(r["actual_generation_mw"]),
            "signed_error_mw": _f(r["signed_error_mw"]),
            "absolute_error_mw": _f(r["absolute_error_mw"]),
            "selected_publish_time_utc": _ts(r["selected_publish_time_utc"]),
            "selection_status": r["selection_status"],
            "data_quality_status": r["data_quality_status"],
            "n_eligible_revisions": int(r["n_eligible_revisions"]),
            "n_later_revisions": int(r["n_later_revisions"]),
        })
    return out


def _m(data: LoadedData, s: Settings) -> int:
    return resolve_resolution(s.evaluation_resolution, data.forecasts.frame)


def _cutoff_info(s: Settings, day: date) -> dict:
    c = decision_cutoff_utc(day, s.cutoff_local_time, s.cutoff_days_before)
    return {"decision_cutoff_utc": _ts(c), "decision_cutoff_local": _ts(c.tz_convert(LONDON)),
            "cutoff_rule": f"{s.cutoff_local_time:%H:%M} Europe/London, {s.cutoff_days_before} day(s) before delivery (configurable assumption)"}


def day_payload(data: LoadedData, day: date, s: Settings) -> dict:
    rec = build_day_records(data.actuals.frame, data.forecasts.frame, day, s.cutoff_local_time, s.cutoff_days_before, _m(data, s))
    summ = summarise(rec)
    matched = rec[rec["data_quality_status"] == OK]
    return {
        "status": status_of(summ["coverage"]), "delivery_date": day.isoformat(), "timezone": TZ, "units": UNITS, "resolution": describe(_m(data, s)),
        **_cutoff_info(s, day),
        "latest_selected_publish_time_utc": _ts(rec["selected_publish_time_utc"].max()),
        "mean_forecast_mw": _f(rec["selected_forecast_mw"].mean()),
        "mean_actual_matched_mw": _f(matched["actual_generation_mw"].mean()),
        "metrics": summ["metrics"], "coverage": summ["coverage"],
        "warnings": quality_report(rec, data.actuals, data.forecasts)["warnings"],
        "data_retrieved_at": _ts(data.fetched_at), "records": records_json(rec),
    }


def error_distribution(rec: pd.DataFrame, top_n: int = 10) -> dict:
    ok = rec[rec["data_quality_status"] == OK]
    if ok.empty:
        return {"n": 0, "over_forecast_intervals": 0, "under_forecast_intervals": 0, "exact_intervals": 0,
                "abs_error_percentiles_mw": None, "signed_error_histogram": None, "largest_errors": []}
    err, ab = ok["signed_error_mw"].to_numpy(float), ok["absolute_error_mw"].to_numpy(float)
    counts, edges = np.histogram(err, bins=10)
    top = ok.sort_values(["absolute_error_mw", "delivery_start_utc"], ascending=[False, True]).head(top_n)
    return {
        "n": int(len(ok)),
        "over_forecast_intervals": int((err > 0).sum()), "under_forecast_intervals": int((err < 0).sum()),
        "exact_intervals": int((err == 0).sum()),
        "abs_error_percentiles_mw": {f"p{q}": float(np.percentile(ab, q)) for q in (50, 90, 95, 100)},
        "signed_error_histogram": {"bin_edges_mw": [float(e) for e in edges], "counts": [int(c) for c in counts]},
        "largest_errors": records_json(top),
    }


def errors_payload(data: LoadedData, day: date, s: Settings) -> dict:
    rec = build_day_records(data.actuals.frame, data.forecasts.frame, day, s.cutoff_local_time, s.cutoff_days_before, _m(data, s))
    cov = coverage(rec)
    return {"status": status_of(cov), "delivery_date": day.isoformat(), "timezone": TZ, "units": UNITS,
            "resolution": describe(_m(data, s)), **_cutoff_info(s, day), "coverage": cov, "distribution": error_distribution(rec),
            "records": records_json(rec), "data_retrieved_at": _ts(data.fetched_at)}


def range_payload(data: LoadedData, start: date, end: date, s: Settings) -> dict:
    rec = build_range_records(data.actuals.frame, data.forecasts.frame, start, end, s.cutoff_local_time, s.cutoff_days_before, _m(data, s))
    summ = summarise(rec)
    return {"status": status_of(summ["coverage"]), "start": start.isoformat(), "end": end.isoformat(),
            "timezone": TZ, "units": UNITS, "resolution": describe(_m(data, s)), "cutoff_rule": _cutoff_info(s, end)["cutoff_rule"],
            "metrics": summ["metrics"], "coverage": summ["coverage"], "daily": summ["daily"],
            "caveat": "A single month does not establish long-term forecast performance.",
            "data_retrieved_at": _ts(data.fetched_at)}


def quality_payload(data: LoadedData, start: date, end: date, s: Settings) -> dict:
    rec = build_range_records(data.actuals.frame, data.forecasts.frame, start, end, s.cutoff_local_time, s.cutoff_days_before, _m(data, s))
    q = quality_report(rec, data.actuals, data.forecasts)
    return {"status": status_of(coverage(rec)), "start": start.isoformat(), "end": end.isoformat(),
            "retrieval_status": "ok", "resolution": describe(_m(data, s)), "data_retrieved_at": _ts(data.fetched_at),
            "forecast_publish_window_utc": [_ts(data.publish_from), _ts(data.publish_to)],
            "source_actual_rows": int(len(data.actuals.frame)), "source_forecast_rows": int(len(data.forecasts.frame)),
            **q}


def revisions_payload(data: LoadedData, day: date, interval_start: pd.Timestamp, s: Settings) -> dict:
    cutoff = decision_cutoff_utc(day, s.cutoff_local_time, s.cutoff_days_before)
    h = revision_history(data.forecasts.frame, interval_start, cutoff)
    revs = [{"publish_time_utc": _ts(r["publish_time_utc"]), "forecast_mw": _f(r["forecast_generation_mw"]),
             "lead_time_hours": _f(r["lead_time_hours"]), "role": r["role"]} for r in h.to_dict("records")]
    return {"delivery_start_utc": _ts(interval_start), "decision_cutoff_utc": _ts(cutoff),
            "includes_post_cutoff_revisions": data.includes_post_cutoff_revisions, "revisions": revs}
