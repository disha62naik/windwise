# Demo script (max 10 min total; record it yourself and upload as an unlisted YouTube video)

Use only numbers the running app actually shows. Do not quote savings or cost reductions.

## Part 1 – Client-facing (≤ 5 min)
1. **Problem (45 s):** Buyers must commit day-ahead volumes before delivery; wind is weather-dependent, so the forecast available at decision time matters.
2. **Dashboard (60 s):** Pick a January delivery date. Show the decision cutoff, latest eligible publication time, and coverage.
3. **Forecast vs actual (60 s):** Point out gaps (missing data is not interpolated).
4. **Errors (60 s):** Explain `error = forecast − actual`; show over/under counts and the largest errors.
5. **Historical accuracy (45 s):** MAE/RMSE/bias/MAPE for the month, daily table. State that one month is not long-term proof.
6. **Data quality & limits (30 s):** Show the panel; mention the cutoff is an assumption.

## Part 2 – Technical (≤ 5 min)
1. **Architecture (45 s):** React/TS → FastAPI → Elexon (FUELHH, WINDFOR); pure-pandas core.
2. **Forecast selection (90 s):** `forecast_selector.py`; cutoff inclusive; later revisions ignored; publish window starts before the month. Show `test_forecast_selector.py`.
3. **Look-ahead prevention (45 s):** `forecast_publish_window` ends at the last cutoff; the revisions audit view is the only place post-cutoff data is fetched.
4. **Normalisation & metrics (45 s):** `normalization.py`, `accuracy.py`; nulls not zeros.
5. **Errors/retries (30 s):** `elexon_client.py` bounded backoff; 502 mapping in `routes.py`.
6. **Tests, Docker, CI, deployment (45 s):** run pytest + `docker compose up --build`; be honest about deployment status.
