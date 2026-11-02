from datetime import date, time

import pandas as pd
import pytest

from app.utils.timestamps import decision_cutoff_utc, expected_intervals, to_utc


def test_interval_counts_across_dst():
    assert len(expected_intervals(date(2026, 1, 15))) == 48
    assert len(expected_intervals(date(2026, 3, 29))) == 46   # clocks forward
    assert len(expected_intervals(date(2026, 10, 25))) == 50  # clocks back


def test_january_day_is_gmt_aligned():
    idx = expected_intervals(date(2026, 1, 15))
    assert idx[0] == pd.Timestamp("2026-01-15T00:00:00Z")
    assert idx[-1] == pd.Timestamp("2026-01-15T23:30:00Z")


def test_bst_day_starts_previous_utc_evening():
    assert expected_intervals(date(2026, 7, 1))[0] == pd.Timestamp("2026-06-30T23:00:00Z")


def test_cutoff_gmt_and_bst():
    assert decision_cutoff_utc(date(2026, 1, 15), time(9, 20)) == pd.Timestamp("2026-01-14T09:20:00Z")
    assert decision_cutoff_utc(date(2026, 7, 2), time(9, 20)) == pd.Timestamp("2026-07-01T08:20:00Z")


def test_cutoff_in_dst_gap_raises():
    with pytest.raises(ValueError):
        decision_cutoff_utc(date(2026, 3, 30), time(1, 30))   # 01:30 on 29 Mar 2026 does not exist


def test_naive_timestamp_rejected():
    with pytest.raises(ValueError):
        to_utc("2026-01-01T00:00:00")
    assert to_utc("2026-01-01T01:00:00+01:00") == pd.Timestamp("2026-01-01T00:00:00Z")
