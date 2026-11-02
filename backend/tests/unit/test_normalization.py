from app.services.normalization import normalize_actuals, normalize_forecasts


def act(start, gen, fuel="WIND", pub=None):
    return {"startTime": start, "generation": gen, "fuelType": fuel, "publishTime": pub}


def fc(start, pub, gen):
    return {"startTime": start, "publishTime": pub, "generation": gen}


def test_actuals_filter_wind_and_ignore_others():
    r = normalize_actuals([act("2026-01-01T00:00:00Z", 100), act("2026-01-01T00:00:00Z", 5, "CCGT")])
    assert len(r.frame) == 1 and r.ignored_non_wind == 1
    assert r.frame.loc[0, "actual_generation_mw"] == 100.0


def test_actuals_missing_negative_and_naive_are_invalid_not_zero():
    r = normalize_actuals([
        act("2026-01-01T00:00:00Z", None),
        act("2026-01-01T00:30:00Z", -5),
        act("2026-01-01T01:00:00", 5),
        act("2026-01-01T01:30:00Z", "abc"),
        act("2026-01-01T02:00:00Z", 0),            # genuine zero is valid
    ])
    assert len(r.invalid) == 4
    assert list(r.frame["actual_generation_mw"]) == [0.0]


def test_actual_duplicate_keeps_latest_publish_time():
    r = normalize_actuals([
        act("2026-01-01T00:00:00Z", 100, pub="2026-01-01T01:00:00Z"),
        act("2026-01-01T00:00:00Z", 110, pub="2026-01-01T03:00:00Z"),
        act("2026-01-01T00:00:00Z", 105, pub="2026-01-01T02:00:00Z"),
    ])
    assert list(r.frame["actual_generation_mw"]) == [110.0] and r.duplicates_collapsed == 2


def test_forecast_revisions_are_kept():
    r = normalize_forecasts([
        fc("2026-01-02T00:00:00Z", "2026-01-01T02:30:00Z", 100),
        fc("2026-01-02T00:00:00Z", "2026-01-01T07:30:00Z", 120),
    ])
    assert len(r.frame) == 2 and r.duplicates_collapsed == 0


def test_forecast_exact_duplicate_and_conflict():
    r = normalize_forecasts([
        fc("2026-01-02T00:00:00Z", "2026-01-01T02:30:00Z", 100),
        fc("2026-01-02T00:00:00Z", "2026-01-01T02:30:00Z", 100),
        fc("2026-01-02T00:00:00Z", "2026-01-01T02:30:00Z", 101),
    ])
    assert len(r.frame) == 1 and r.duplicates_collapsed == 2 and r.conflicting_duplicates == 1
    assert r.frame.loc[0, "forecast_generation_mw"] == 101.0


def test_forecast_missing_publish_time_invalid():
    r = normalize_forecasts([{"startTime": "2026-01-02T00:00:00Z", "generation": 5}])
    assert len(r.invalid) == 1 and r.frame.empty


def test_empty_inputs_have_expected_columns():
    a, f = normalize_actuals([]), normalize_forecasts([])
    assert a.frame.empty and "actual_generation_mw" in a.frame.columns
    assert f.frame.empty and "publish_time_local" in f.frame.columns


def test_local_time_columns_are_london():
    r = normalize_forecasts([fc("2026-07-01T00:00:00Z", "2026-06-30T08:00:00Z", 1)])
    assert r.frame.loc[0, "delivery_start_local"].hour == 1   # BST = UTC+1
