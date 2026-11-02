from datetime import date, time

import pandas as pd
import pytest

from app.config import Settings
from app.services.analysis import build_day_records, summarise
from app.services.data_loader import LoadedData
from app.services.normalization import normalize_actuals, normalize_forecasts
from app.services.payloads import day_payload
from app.services.resolution import aggregate_actuals, detect_forecast_resolution_minutes, resolve_resolution

NOW = pd.Timestamp("2026-02-01T00:00:00Z")


def A(rows):
    return normalize_actuals([{"startTime": t, "generation": g, "fuelType": "WIND"} for t, g in rows])


def F(rows):
    return normalize_forecasts([{"startTime": t, "publishTime": p, "generation": g} for t, p, g in rows])


def test_detection_hourly_halfhourly_empty_and_unsupported():
    hourly = F([("2026-01-15T09:00:00Z", "2026-01-14T07:30:00Z", 1), ("2026-01-15T10:00:00Z", "2026-01-14T07:30:00Z", 1)])
    half = F([("2026-01-15T09:00:00Z", "2026-01-14T07:30:00Z", 1), ("2026-01-15T09:30:00Z", "2026-01-14T07:30:00Z", 1)])
    assert detect_forecast_resolution_minutes(hourly.frame) == 60
    assert detect_forecast_resolution_minutes(half.frame) == 30
    assert detect_forecast_resolution_minutes(F([]).frame) is None
    assert resolve_resolution("auto", F([]).frame) == 30 and resolve_resolution("60", half.frame) == 60
    with pytest.raises(ValueError):
        detect_forecast_resolution_minutes(F([("2026-01-15T09:15:00Z", "2026-01-14T07:30:00Z", 1)]).frame)


def test_hourly_aggregation_is_mean_and_incomplete_hours_dropped():
    a = A([("2026-01-15T09:00:00Z", 4200), ("2026-01-15T09:30:00Z", 4350), ("2026-01-15T10:00:00Z", 4500)])
    out = aggregate_actuals(a.frame, 60)
    assert list(out["actual_generation_mw"]) == [4275.0]          # 10:00 hour has only one half-hour -> dropped
    assert aggregate_actuals(a.frame, 30).shape[0] == 3            # native untouched


def test_hourly_record_error_is_hand_calculated():
    a = A([("2026-01-15T09:00:00Z", 4200), ("2026-01-15T09:30:00Z", 4350)])
    f = F([("2026-01-15T09:00:00Z", "2026-01-14T07:30:00Z", 4100)])
    rec = build_day_records(a.frame, f.frame, date(2026, 1, 15), time(9, 20), 1, minutes=60)
    assert len(rec) == 24
    m = summarise(rec)["metrics"]
    assert m["n_matched"] == 1 and m["bias_mw"] == pytest.approx(-175.0) and m["mae_mw"] == pytest.approx(175.0)


def test_hourly_dst_day_lengths_and_empty_inputs():
    a, f = A([]), F([])
    assert len(build_day_records(a.frame, f.frame, date(2026, 3, 29), time(9, 20), 1, minutes=60)) == 23
    assert len(build_day_records(a.frame, f.frame, date(2026, 10, 25), time(9, 20), 1, minutes=60)) == 25


def test_auto_resolution_in_payload_and_no_interpolation():
    a = A([("2026-01-15T00:00:00Z", 100), ("2026-01-15T00:30:00Z", 120)])
    f = F([("2026-01-15T00:00:00Z", "2026-01-14T07:30:00Z", 90),
           ("2026-01-15T00:00:00Z", "2026-01-14T15:30:00Z", 110)])     # post-cutoff revision ignored
    p = day_payload(LoadedData(a, f, NOW, NOW, NOW), date(2026, 1, 15), Settings())
    assert p["resolution"]["minutes"] == 60 and p["coverage"]["expected_intervals"] == 24
    assert p["metrics"]["bias_mw"] == pytest.approx(90 - 110)           # actual hour mean = 110
    assert p["coverage"]["forecast_intervals"] == 1                     # no invented forecasts
