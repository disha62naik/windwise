"""End-to-end over the pure pipeline (normalise -> select -> align -> metrics)."""
from datetime import date, time

import pytest

from app.services.analysis import build_day_records, quality_report, summarise
from app.services.normalization import normalize_actuals, normalize_forecasts

CUTOFF = time(9, 20)


def build():
    actuals = normalize_actuals([
        {"startTime": "2026-01-15T00:00:00Z", "generation": 100, "fuelType": "WIND"},
        {"startTime": "2026-01-15T00:30:00Z", "generation": 90, "fuelType": "WIND"},
        {"startTime": "2026-01-15T01:00:00Z", "generation": 200, "fuelType": "WIND"},
        {"startTime": "2026-01-15T01:30:00Z", "generation": None, "fuelType": "WIND"},
    ])
    forecasts = normalize_forecasts([
        {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-13T22:30:00Z", "generation": 50},
        {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-14T07:30:00Z", "generation": 110},
        {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-14T15:30:00Z", "generation": 100},  # look-ahead trap
        {"startTime": "2026-01-15T01:00:00Z", "publishTime": "2026-01-14T07:30:00Z", "generation": 180},
    ])
    return actuals, forecasts


def test_records_and_metrics_use_only_eligible_forecasts():
    actuals, forecasts = build()
    rec = build_day_records(actuals.frame, forecasts.frame, date(2026, 1, 15), CUTOFF)
    assert len(rec) == 48
    s = summarise(rec)
    # matched: 00:00 (110 vs 100 => +10) and 01:00 (180 vs 200 => -20). The 15:30 revision would give 0 error.
    assert s["coverage"]["matched_intervals"] == 2
    assert s["metrics"]["mae_mw"] == pytest.approx(15.0)
    assert s["metrics"]["bias_mw"] == pytest.approx(-5.0)
    assert s["metrics"]["rmse_mw"] == pytest.approx((250) ** 0.5)


def test_status_and_quality_report():
    actuals, forecasts = build()
    rec = build_day_records(actuals.frame, forecasts.frame, date(2026, 1, 15), CUTOFF)
    by_ts = rec.set_index("delivery_start_utc")["data_quality_status"]
    import pandas as pd
    assert by_ts[pd.Timestamp("2026-01-15T00:30:00Z")] == "NO_FORECAST"      # actual only
    assert by_ts[pd.Timestamp("2026-01-15T05:00:00Z")] == "MISSING_BOTH"
    q = quality_report(rec, actuals, forecasts)
    assert q["expected_intervals"] == 48 and q["actual_intervals"] == 3
    assert q["invalid_actual_records"] == 1 and q["warnings"]


def test_empty_inputs_give_null_metrics_not_zero():
    a, f = normalize_actuals([]), normalize_forecasts([])
    s = summarise(build_day_records(a.frame, f.frame, date(2026, 1, 15), CUTOFF))
    assert s["metrics"]["mae_mw"] is None and s["coverage"]["matched_intervals"] == 0
