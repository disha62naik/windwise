from app.services.report import render_markdown


def test_report_shows_na_for_null_metrics_never_zero():
    m = dict(n_matched=0, mae_mw=None, rmse_mw=None, bias_mw=None, median_abs_error_mw=None,
             mape_pct=None, mape_n=0, mape_excluded_zero_actual=0)
    cov = dict(expected_intervals=24, actual_intervals=0, forecast_intervals=0, matched_intervals=0,
               missing_forecast_intervals=24, missing_actual_intervals=24, intervals_with_only_later_forecasts=0)
    q = dict(invalid_actual_records=0, invalid_forecast_records=0, duplicate_actual_records_collapsed=0,
             duplicate_forecast_records_collapsed=0, conflicting_forecast_duplicates=0, warnings=["w"])
    v = {k: "x" for k in ["actual_rows", "actual_fields", "actual_fuel_types", "actual_start_minutes", "actual_range_mw",
                          "forecast_rows", "forecast_fields", "forecast_start_minutes", "forecast_range_mw", "publish_range"]}
    p = dict(start="2026-01-01", end="2026-01-01", retrieved_at="t", cutoff_local_time="09:20", cutoff_days_before=1,
             publish_from="a", publish_to="b", resolution={"minutes": 60, "method": "hourly"})
    md = render_markdown(p, v, {"metrics": m, "coverage": cov, "daily": []}, q, None)
    assert "| MAE | n/a |" in md and "assumption" in md and "⚠ w" in md
