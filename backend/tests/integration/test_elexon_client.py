"""Needs httpx (not installable in the authoring sandbox -> NOT yet executed there)."""
import httpx
import pytest

from app.clients.elexon_client import ElexonClient, ElexonError, ElexonResponseError
from app.config import Settings


def make(handler, retries=2):
    s = Settings(max_retries=retries)
    c = httpx.Client(base_url=s.elexon_base_url, transport=httpx.MockTransport(handler))
    sleeps = []
    return ElexonClient(s, c, sleep=sleeps.append), sleeps


def test_retries_transient_then_succeeds():
    calls = {"n": 0}
    def h(req):
        calls["n"] += 1
        return httpx.Response(503) if calls["n"] < 3 else httpx.Response(200, json=[{"a": 1}])
    client, sleeps = make(h)
    assert client._get_records("/x", {}) == [{"a": 1}]
    assert sleeps == [1.0, 2.0]


def test_no_retry_on_400():
    calls = {"n": 0}
    def h(req):
        calls["n"] += 1
        return httpx.Response(400)
    client, _ = make(h)
    with pytest.raises(ElexonError):
        client._get_records("/x", {})
    assert calls["n"] == 1


def test_gives_up_after_bounded_retries():
    client, _ = make(lambda r: httpx.Response(500), retries=2)
    with pytest.raises(ElexonError):
        client._get_records("/x", {})


def test_malformed_body_rejected():
    client, _ = make(lambda r: httpx.Response(200, json={"oops": 1}))
    with pytest.raises(ElexonResponseError):
        client._get_records("/x", {})
