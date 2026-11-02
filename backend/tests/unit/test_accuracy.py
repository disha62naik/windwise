import math

import pandas as pd
import pytest

from app.services.accuracy import add_error_columns, compute_metrics


def S(values):
    return pd.Series(values, dtype="float64")


def test_perfect_forecast():
    m = compute_metrics(S([5, 10, 15]), S([5, 10, 15]))
    assert (m.mae_mw, m.rmse_mw, m.bias_mw, m.mape_pct) == (0.0, 0.0, 0.0, 0.0)
    assert m.n_matched == 3


def test_hand_calculated_metrics_and_cancelling_bias():
    # errors: +10, -10, 0  -> MAE 20/3, RMSE sqrt(200/3), bias 0 (errors cancel)
    m = compute_metrics(S([110, 90, 100]), S([100, 100, 100]))
    assert m.mae_mw == pytest.approx(20 / 3)
    assert m.rmse_mw == pytest.approx(math.sqrt(200 / 3))
    assert m.bias_mw == pytest.approx(0.0)
    assert m.mape_pct == pytest.approx(20 / 3)
    assert m.median_abs_error_mw == pytest.approx(10.0)


def test_sign_convention_over_and_under_forecast():
    assert compute_metrics(S([120]), S([100])).bias_mw == pytest.approx(20.0)    # over
    assert compute_metrics(S([80]), S([100])).bias_mw == pytest.approx(-20.0)    # under


def test_mape_excludes_zero_actual_and_reports_count():
    # errors +10 (actual 0, excluded from MAPE), -20 (actual 40 -> 50%)
    m = compute_metrics(S([10, 20]), S([0, 40]))
    assert m.mae_mw == pytest.approx(15.0)
    assert m.bias_mw == pytest.approx(-5.0)
    assert m.rmse_mw == pytest.approx(math.sqrt(250))
    assert m.mape_pct == pytest.approx(50.0)
    assert (m.mape_n, m.mape_excluded_zero_actual) == (1, 1)


def test_mape_none_when_all_actuals_zero():
    m = compute_metrics(S([5, 5]), S([0, 0]))
    assert m.mape_pct is None and m.mae_mw == pytest.approx(5.0)


def test_missing_values_not_treated_as_zero():
    m = compute_metrics(S([1, float("nan"), 3, 4]), S([1, 2, float("nan"), 6]))
    assert m.n_matched == 2                       # rows 0 and 3 only
    assert m.mae_mw == pytest.approx(1.0)         # (0 + 2) / 2


def test_invalid_numbers_excluded():
    m = compute_metrics(pd.Series([1, "x", float("inf")]), pd.Series([1, 1, 1]))
    assert m.n_matched == 1


def test_empty_returns_none_not_zero():
    m = compute_metrics(S([]), S([]))
    assert m.n_matched == 0
    assert m.mae_mw is None and m.rmse_mw is None and m.bias_mw is None and m.mape_pct is None


def test_error_columns_nan_for_unmatched():
    df = add_error_columns(pd.DataFrame({"f": [10.0, None], "a": [4.0, 5.0]}), "f", "a")
    assert df.loc[0, "signed_error_mw"] == 6.0
    assert df.loc[0, "squared_error_mw2"] == 36.0
    assert math.isnan(df.loc[1, "signed_error_mw"])
