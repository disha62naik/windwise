"""Response schemas (OpenAPI docs). Unavailable metrics are null, never 0."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

Status = Literal["ok", "partial", "empty"]


class Metrics(BaseModel):
    n_matched: int
    mae_mw: Optional[float] = None
    rmse_mw: Optional[float] = None
    bias_mw: Optional[float] = None
    median_abs_error_mw: Optional[float] = None
    mape_pct: Optional[float] = None
    mape_n: int = 0
    mape_excluded_zero_actual: int = 0


class Coverage(BaseModel):
    expected_intervals: int
    actual_intervals: int
    forecast_intervals: int
    matched_intervals: int
    missing_forecast_intervals: int
    missing_actual_intervals: int
    intervals_with_only_later_forecasts: int


class IntervalRecord(BaseModel):
    delivery_start_utc: str
    delivery_start_local: str
    delivery_date: str
    forecast_mw: Optional[float] = None
    actual_mw: Optional[float] = None
    signed_error_mw: Optional[float] = None
    absolute_error_mw: Optional[float] = None
    selected_publish_time_utc: Optional[str] = None
    selection_status: str
    data_quality_status: str
    n_eligible_revisions: int
    n_later_revisions: int


class DayForecastResponse(BaseModel):
    status: Status
    delivery_date: str
    timezone: str
    units: dict[str, str]
    decision_cutoff_utc: str
    decision_cutoff_local: str
    cutoff_rule: str
    resolution: Optional[dict] = None
    latest_selected_publish_time_utc: Optional[str] = None
    mean_forecast_mw: Optional[float] = None
    mean_actual_matched_mw: Optional[float] = None
    metrics: Metrics
    coverage: Coverage
    warnings: list[str]
    data_retrieved_at: Optional[str] = None
    records: list[IntervalRecord]


class ErrorsResponse(BaseModel):
    status: Status
    delivery_date: str
    timezone: str
    units: dict[str, str]
    decision_cutoff_utc: str
    decision_cutoff_local: str
    cutoff_rule: str
    resolution: Optional[dict] = None
    coverage: Coverage
    distribution: dict
    records: list[IntervalRecord]
    data_retrieved_at: Optional[str] = None


class DailySummary(Metrics):
    delivery_date: str
    expected_intervals: int
    actual_intervals: int
    forecast_intervals: int
    matched_intervals: int
    missing_forecast_intervals: int
    missing_actual_intervals: int
    intervals_with_only_later_forecasts: int


class AccuracyResponse(BaseModel):
    status: Status
    start: str
    end: str
    timezone: str
    units: dict[str, str]
    cutoff_rule: str
    resolution: Optional[dict] = None
    metrics: Metrics
    coverage: Coverage
    daily: list[DailySummary]
    caveat: str
    data_retrieved_at: Optional[str] = None


class DataQualityResponse(Coverage):
    status: Status
    start: str
    end: str
    retrieval_status: str
    resolution: Optional[dict] = None
    data_retrieved_at: Optional[str] = None
    forecast_publish_window_utc: list[Optional[str]]
    source_actual_rows: int
    source_forecast_rows: int
    invalid_actual_records: int
    invalid_forecast_records: int
    duplicate_actual_records_collapsed: int
    duplicate_forecast_records_collapsed: int
    conflicting_forecast_duplicates: int
    non_wind_records_ignored: int
    warnings: list[str]


class Revision(BaseModel):
    publish_time_utc: Optional[str] = None
    forecast_mw: Optional[float] = None
    lead_time_hours: Optional[float] = None
    role: Literal["SELECTED", "EARLIER_ELIGIBLE", "LATER_UNAVAILABLE"]


class RevisionsResponse(BaseModel):
    delivery_start_utc: str
    decision_cutoff_utc: str
    includes_post_cutoff_revisions: bool
    revisions: list[Revision]


class ErrorBody(BaseModel):
    detail: str
