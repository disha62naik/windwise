"""API tests with a fake DataService. Requires fastapi + httpx (NOT run in the authoring sandbox)."""
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_service
from app.clients.elexon_client import ElexonError
from app.config import Settings
from app.main import app
from app.services.data_loader import LoadedData
from app.services.normalization import normalize_actuals, normalize_forecasts

NOW = pd.Timestamp("2026-02-01T00:00:00Z")


class FakeService:
    settings = Settings(evaluation_resolution="30")
    fail = False

    def get_range(self, start, end, include_later=False):
        if self.fail:
            raise ElexonError("Elexon unavailable after 4 attempts")
        a = normalize_actuals([{"startTime": "2026-01-15T00:00:00Z", "generation": 100, "fuelType": "WIND"}])
        f = normalize_forecasts([
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-14T07:30:00Z", "generation": 110},
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-14T15:30:00Z", "generation": 100}])
        return LoadedData(a, f, NOW, NOW, NOW, include_later)


@pytest.fixture
def svc():
    s = FakeService()
    app.dependency_overrides[get_service] = lambda: s
    yield s
    app.dependency_overrides.clear()


client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_forecast_endpoint(svc):
    r = client.get("/api/forecast", params={"date": "2026-01-15"})
    assert r.status_code == 200
    body = r.json()
    assert body["metrics"]["mae_mw"] == 10.0 and body["records"][0]["forecast_mw"] == 110.0


def test_invalid_date_and_month_rejected(svc):
    assert client.get("/api/forecast", params={"date": "nope"}).status_code == 422
    assert client.get("/api/overview", params={"month": "2026-13"}).status_code == 422
    assert client.get("/api/accuracy", params={"start": "2026-01-10", "end": "2026-01-01"}).status_code == 422
    assert client.get("/api/accuracy", params={"start": "2025-01-01", "end": "2026-01-01"}).status_code == 422


def test_upstream_failure_is_controlled_502(svc):
    svc.fail = True
    r = client.get("/api/forecast", params={"date": "2026-01-15"})
    assert r.status_code == 502 and "Traceback" not in r.text


def test_revisions_endpoint(svc):
    r = client.get("/api/revisions", params={"date": "2026-01-15", "interval_start": "2026-01-15T00:00:00Z"})
    assert [x["role"] for x in r.json()["revisions"]] == ["SELECTED", "LATER_UNAVAILABLE"]
    assert client.get("/api/revisions", params={"date": "2026-01-15", "interval_start": "2026-01-15T00:00:00"}).status_code == 422


def test_overview_and_quality(svc):
    assert client.get("/api/overview?month=2026-01").status_code == 200
    assert client.get("/api/data-quality?month=2026-01").status_code == 200
