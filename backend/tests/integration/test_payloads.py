from datetime import date

import pandas as pd
import pytest

from app.config import Settings
from app.services.data_loader import LoadedData, forecast_publish_window, month_bounds
from app.services.normalization import normalize_actuals, normalize_forecasts
from app.services.payloads import day_payload, errors_payload, quality_payload, range_payload, revisions_payload

S = Settings(evaluation_resolution="30")
NOW = pd.Timestamp("2026-02-01T00:00:00Z")


def loaded(include_later=False):
    a = normalize_actuals([
        {"startTime": "2026-01-15T00:00:00Z", "generation": 100, "fuelType": "WIND"},
        {"startTime": "2026-01-15T01:00:00Z", "generation": 200, "fuelType": "WIND"},
        {"startTime": "2026-01-15T02:00:00Z", "generation": 0, "fuelType": "WIND"},
    ])
    f = normalize_forecasts([
        {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-14T07:30:00Z", "generation": 110},
        {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-14T11:30:00Z", "generation": 100},
        {"startTime": "2026-01-15T01:00:00Z", "publishTime": "2026-01-14T07:30:00Z", "generation": 180},
        {"startTime": "2026-01-15T02:00:00Z", "publishTime": "2026-01-14T07:30:00Z", "generation": 30},
    ])
    return LoadedData(a, f, NOW, NOW, NOW, include_later)


def test_day_payload_values_and_nulls():
    p = day_payload(loaded(), date(2026, 1, 15), S)
    assert p["status"] == "partial"                      # 45 expected intervals lack actuals
    assert p["coverage"]["matched_intervals"] == 3 and p["coverage"]["expected_intervals"] == 48
    assert p["metrics"]["bias_mw"] == pytest.approx((10 - 20 + 30) / 3)
    assert p["metrics"]["mape_n"] == 2 and p["metrics"]["mape_excluded_zero_actual"] == 1
    assert p["decision_cutoff_utc"].startswith("2026-01-14T09:20:00")
    assert p["latest_selected_publish_time_utc"].startswith("2026-01-14T07:30:00")
    assert p["mean_forecast_mw"] == pytest.approx((110 + 180 + 30) / 3)
    first = p["records"][0]
    assert first["forecast_mw"] == 110.0 and first["n_later_revisions"] == 1
    assert p["records"][5]["forecast_mw"] is None and p["records"][5]["signed_error_mw"] is None


def test_empty_day_payload_is_null_not_zero():
    a, f = normalize_actuals([]), normalize_forecasts([])
    p = day_payload(LoadedData(a, f, NOW, NOW, NOW), date(2026, 1, 15), S)
    assert p["status"] == "empty" and p["metrics"]["mae_mw"] is None and p["mean_forecast_mw"] is None


def test_errors_payload_distribution():
    d = errors_payload(loaded(), date(2026, 1, 15), S)["distribution"]
    assert (d["over_forecast_intervals"], d["under_forecast_intervals"]) == (2, 1)
    assert d["largest_errors"][0]["absolute_error_mw"] == 30.0
    assert sum(d["signed_error_histogram"]["counts"]) == 3


def test_range_and_quality_payloads():
    r = range_payload(loaded(), date(2026, 1, 15), date(2026, 1, 16), S)
    assert len(r["daily"]) == 2 and r["coverage"]["expected_intervals"] == 96
    q = quality_payload(loaded(), date(2026, 1, 15), date(2026, 1, 15), S)
    assert q["actual_intervals"] == 3 and q["warnings"]


def test_revisions_payload_labels_later_revision():
    p = revisions_payload(loaded(True), date(2026, 1, 15), pd.Timestamp("2026-01-15T00:00:00Z"), S)
    assert [r["role"] for r in p["revisions"]] == ["SELECTED", "LATER_UNAVAILABLE"]


def test_publish_window_covers_december_and_stops_at_cutoff():
    lo, hi = forecast_publish_window(date(2026, 1, 1), date(2026, 1, 31), S)
    assert lo == pd.Timestamp("2025-12-24T09:20:00Z")      # Dec 31 09:20 - 7 days
    assert hi == pd.Timestamp("2026-01-30T09:20:00Z")      # last cutoff, nothing later
    _, hi2 = forecast_publish_window(date(2026, 1, 1), date(2026, 1, 31), S, include_later=True)
    assert hi2 == pd.Timestamp("2026-02-01T00:00:00Z")


def test_month_bounds():
    assert month_bounds(date(2026, 2, 10)) == (date(2026, 2, 1), date(2026, 2, 28))
