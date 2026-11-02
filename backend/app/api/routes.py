"""HTTP layer only: validation, error mapping, delegation to pure payload builders."""
from __future__ import annotations

import logging
from datetime import date, datetime
from functools import lru_cache

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from app.clients.elexon_client import ElexonClient, ElexonError
from app.config import Settings
from app.schemas import analytics as sc
from app.services import payloads
from app.services.data_loader import DataService, LoadedData
from app.utils.timestamps import to_utc

log = logging.getLogger("windwise.api")
router = APIRouter(prefix="/api")
MONTH = r"^\d{4}-(0[1-9]|1[0-2])$"
UPSTREAM = {502: {"model": sc.ErrorBody, "description": "Elexon unavailable or returned bad data"}}


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()


@lru_cache
def _service() -> DataService:
    s = get_settings()
    return DataService(ElexonClient(s), s)


def get_service() -> DataService:  # overridden in tests via app.dependency_overrides
    return _service()


def _month_range(month: str) -> tuple[date, date]:
    from app.services.data_loader import month_bounds
    return month_bounds(datetime.strptime(month, "%Y-%m").date())


def _load(service: DataService, start: date, end: date, include_later: bool = False) -> LoadedData:
    s = service.settings
    if end < start:
        raise HTTPException(422, "end must not be before start")
    if (end - start).days + 1 > s.max_range_days:
        raise HTTPException(422, f"range must not exceed {s.max_range_days} days")
    try:
        return service.get_range(start, end, include_later)
    except ElexonError as exc:
        log.error("upstream failure: %s", exc)
        raise HTTPException(502, str(exc)) from exc


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/forecast", response_model=sc.DayForecastResponse, responses=UPSTREAM)
def forecast(date: date, service: DataService = Depends(get_service)):
    return payloads.day_payload(_load(service, date, date), date, service.settings)


@router.get("/forecast-errors", response_model=sc.ErrorsResponse, responses=UPSTREAM)
def forecast_errors(date: date, service: DataService = Depends(get_service)):
    return payloads.errors_payload(_load(service, date, date), date, service.settings)


@router.get("/accuracy", response_model=sc.AccuracyResponse, responses=UPSTREAM)
def accuracy(start: date, end: date, service: DataService = Depends(get_service)):
    return payloads.range_payload(_load(service, start, end), start, end, service.settings)


@router.get("/overview", response_model=sc.AccuracyResponse, responses=UPSTREAM)
def overview(month: str = Query("2026-01", pattern=MONTH), service: DataService = Depends(get_service)):
    start, end = _month_range(month)
    return payloads.range_payload(_load(service, start, end), start, end, service.settings)


@router.get("/data-quality", response_model=sc.DataQualityResponse, responses=UPSTREAM)
def data_quality(month: str = Query("2026-01", pattern=MONTH), service: DataService = Depends(get_service)):
    start, end = _month_range(month)
    return payloads.quality_payload(_load(service, start, end), start, end, service.settings)


@router.get("/revisions", response_model=sc.RevisionsResponse, responses=UPSTREAM)
def revisions(date: date, interval_start: str, service: DataService = Depends(get_service)):
    """Audit view: every revision for one interval, labelled selected / earlier / later-unavailable."""
    try:
        ts = to_utc(interval_start)
    except ValueError as exc:
        raise HTTPException(422, "interval_start must be a timezone-aware ISO timestamp") from exc
    data = _load(service, date, date, include_later=True)
    return payloads.revisions_payload(data, date, ts, service.settings)
