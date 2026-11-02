from datetime import date, time

import pandas as pd

from app.services.forecast_selector import revision_history, select_forecasts
from app.services.normalization import normalize_forecasts
from app.utils.timestamps import decision_cutoff_utc

D = pd.Timestamp("2026-01-15T12:00:00Z")
CUTOFF = pd.Timestamp("2026-01-14T09:20:00Z")


def frame(rows):
    return normalize_forecasts(
        [{"startTime": "2026-01-15T12:00:00Z", "publishTime": p, "generation": g} for p, g in rows]
    ).frame


def pick(rows):
    return select_forecasts(frame(rows), pd.DatetimeIndex([D]), CUTOFF).iloc[0]


def test_latest_eligible_wins_and_later_revision_ignored():
    r = pick([("2026-01-13T22:30:00Z", 100), ("2026-01-14T07:30:00Z", 150),
              ("2026-01-14T11:30:00Z", 999)])          # after cutoff: must not be used
    assert r["selected_forecast_mw"] == 150.0
    assert r["selected_publish_time_utc"] == pd.Timestamp("2026-01-14T07:30:00Z")
    assert (r["n_eligible_revisions"], r["n_later_revisions"]) == (2, 1)


def test_publication_exactly_at_cutoff_is_eligible():
    assert pick([("2026-01-14T09:20:00Z", 42)])["selected_forecast_mw"] == 42.0


def test_publication_before_the_month_is_used():
    # Published in December for a January delivery interval.
    d = pd.Timestamp("2026-01-01T06:00:00Z")
    f = normalize_forecasts([{"startTime": "2026-01-01T06:00:00Z",
                              "publishTime": "2025-12-31T02:30:00Z", "generation": 77}]).frame
    cutoff = decision_cutoff_utc(date(2026, 1, 1), time(9, 20))
    r = select_forecasts(f, pd.DatetimeIndex([d]), cutoff).iloc[0]
    assert r["selected_forecast_mw"] == 77.0


def test_only_later_forecasts_reports_status_and_no_value():
    r = pick([("2026-01-14T11:30:00Z", 999)])
    assert r["selection_status"] == "ONLY_LATER_FORECASTS"
    assert pd.isna(r["selected_forecast_mw"])


def test_no_forecast_status():
    r = select_forecasts(frame([]), pd.DatetimeIndex([D]), CUTOFF).iloc[0]
    assert r["selection_status"] == "NO_FORECAST_PUBLISHED"


def test_selection_is_independent_of_input_order():
    rows = [("2026-01-14T07:30:00Z", 150), ("2026-01-13T22:30:00Z", 100)]
    assert pick(rows)["selected_forecast_mw"] == pick(rows[::-1])["selected_forecast_mw"] == 150.0


def test_revision_history_labels():
    h = revision_history(
        frame([("2026-01-13T22:30:00Z", 100), ("2026-01-14T07:30:00Z", 150), ("2026-01-14T11:30:00Z", 999)]),
        D, CUTOFF)
    assert list(h["role"]) == ["EARLIER_ELIGIBLE", "SELECTED", "LATER_UNAVAILABLE"]
    assert h.loc[1, "lead_time_hours"] == 28.5 + 0.0 or abs(h.loc[1, "lead_time_hours"] - 28.5) < 1e-9
