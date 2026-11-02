"""Forecast accuracy metrics. error = forecast - actual (positive = over-forecast), MW."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Metrics:
    n_matched: int
    mae_mw: Optional[float]
    rmse_mw: Optional[float]
    bias_mw: Optional[float]
    median_abs_error_mw: Optional[float]
    mape_pct: Optional[float]
    mape_n: int
    mape_excluded_zero_actual: int

    def to_dict(self) -> dict:
        return asdict(self)


def valid_pair_mask(forecast: pd.Series, actual: pd.Series) -> pd.Series:
    f = pd.to_numeric(forecast, errors="coerce")
    a = pd.to_numeric(actual, errors="coerce")
    return np.isfinite(f) & np.isfinite(a)


def compute_metrics(forecast: pd.Series, actual: pd.Series) -> Metrics:
    """Metrics over intervals where BOTH values are finite. Nothing is imputed.

    MAPE additionally excludes actual == 0 (undefined); the count is reported.
    With no eligible pairs every metric is None, never 0.
    """
    f = pd.to_numeric(pd.Series(forecast).reset_index(drop=True), errors="coerce")
    a = pd.to_numeric(pd.Series(actual).reset_index(drop=True), errors="coerce")
    mask = valid_pair_mask(f, a)
    n = int(mask.sum())
    if n == 0:
        return Metrics(0, None, None, None, None, None, 0, 0)
    f, a = f[mask].astype(float), a[mask].astype(float)
    err = f - a
    nonzero = a != 0
    n_mape = int(nonzero.sum())
    mape = float((err[nonzero].abs() / a[nonzero].abs()).mean() * 100) if n_mape else None
    return Metrics(
        n_matched=n,
        mae_mw=float(err.abs().mean()),
        rmse_mw=float(np.sqrt((err ** 2).mean())),
        bias_mw=float(err.mean()),
        median_abs_error_mw=float(err.abs().median()),
        mape_pct=mape,
        mape_n=n_mape,
        mape_excluded_zero_actual=n - n_mape,
    )


def add_error_columns(df: pd.DataFrame, forecast_col: str, actual_col: str) -> pd.DataFrame:
    """Add signed/absolute/squared error; NaN (not 0) where either side is missing."""
    out = df.copy()
    mask = valid_pair_mask(out[forecast_col], out[actual_col])
    err = (pd.to_numeric(out[forecast_col], errors="coerce")
           - pd.to_numeric(out[actual_col], errors="coerce")).where(mask)
    out["signed_error_mw"] = err
    out["absolute_error_mw"] = err.abs()
    out["squared_error_mw2"] = err ** 2
    return out
