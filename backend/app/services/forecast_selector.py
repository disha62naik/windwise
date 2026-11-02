"""Historical forecast selection - the core anti-look-ahead module.

For each delivery interval we choose the most recent forecast whose publish time is
<= the decision cutoff. Anything published later was not knowable at decision time and
is never used, however much "better" it may be.
"""
from __future__ import annotations

from enum import Enum

import pandas as pd


class SelectionStatus(str, Enum):
    SELECTED = "SELECTED"
    NO_FORECAST_PUBLISHED = "NO_FORECAST_PUBLISHED"      # no revision at all for the interval
    ONLY_LATER_FORECASTS = "ONLY_LATER_FORECASTS"        # revisions exist, all after cutoff


def select_forecasts(forecasts: pd.DataFrame, expected_starts: pd.DatetimeIndex,
                     cutoff: pd.Timestamp) -> pd.DataFrame:
    """One row per expected interval with the eligible forecast and an audit trail.

    Eligibility is inclusive (publish_time_utc <= cutoff). Ties on identical publish time
    resolve to the last row in input order after a stable sort (deterministic).
    """
    if cutoff.tzinfo is None:
        raise ValueError("cutoff must be timezone-aware")
    base = pd.DataFrame({"delivery_start_utc": pd.Series(expected_starts).dt.as_unit("ns")})
    relevant = forecasts[forecasts["delivery_start_utc"].isin(expected_starts)]
    eligible = relevant[relevant["publish_time_utc"] <= cutoff]
    later = relevant[relevant["publish_time_utc"] > cutoff]

    chosen = (
        eligible.sort_values(["delivery_start_utc", "publish_time_utc"], kind="mergesort")
        .groupby("delivery_start_utc", as_index=False).tail(1)
        .rename(columns={"forecast_generation_mw": "selected_forecast_mw",
                         "publish_time_utc": "selected_publish_time_utc"})
        [["delivery_start_utc", "selected_forecast_mw", "selected_publish_time_utc"]]
    )
    n_elig = eligible.groupby("delivery_start_utc").size().rename("n_eligible_revisions")
    n_late = later.groupby("delivery_start_utc").size().rename("n_later_revisions")

    out = (base.merge(chosen, on="delivery_start_utc", how="left")
           .merge(n_elig, on="delivery_start_utc", how="left")
           .merge(n_late, on="delivery_start_utc", how="left"))
    out[["n_eligible_revisions", "n_later_revisions"]] = (
        out[["n_eligible_revisions", "n_later_revisions"]].fillna(0).astype(int))
    out["selection_status"] = SelectionStatus.NO_FORECAST_PUBLISHED.value
    out.loc[out["n_later_revisions"] > 0, "selection_status"] = SelectionStatus.ONLY_LATER_FORECASTS.value
    out.loc[out["selected_forecast_mw"].notna(), "selection_status"] = SelectionStatus.SELECTED.value
    out["decision_cutoff_utc"] = cutoff
    return out


def revision_history(forecasts: pd.DataFrame, delivery_start: pd.Timestamp,
                     cutoff: pd.Timestamp) -> pd.DataFrame:
    """All revisions for one interval, labelled for audit.

    role: SELECTED | EARLIER_ELIGIBLE | LATER_UNAVAILABLE. lead_time_hours = delivery - publish.
    """
    rows = forecasts[forecasts["delivery_start_utc"] == delivery_start]
    rows = rows.sort_values("publish_time_utc", kind="mergesort").reset_index(drop=True).copy()
    rows["role"] = "LATER_UNAVAILABLE"
    eligible_idx = rows.index[rows["publish_time_utc"] <= cutoff]
    rows.loc[eligible_idx, "role"] = "EARLIER_ELIGIBLE"
    if len(eligible_idx):
        rows.loc[eligible_idx[-1], "role"] = "SELECTED"
    rows["lead_time_hours"] = (delivery_start - rows["publish_time_utc"]).dt.total_seconds() / 3600.0
    return rows
