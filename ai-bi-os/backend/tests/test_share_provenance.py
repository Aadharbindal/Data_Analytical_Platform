"""Tests for the public drilldown behind a shared dashboard.

The cases that matter are the gate and the arithmetic: a link that is expired,
revoked or password-protected must not hand over the underlying rows, and the
figure recomputed from the rows shown must equal the figure on the card. A
drilldown that quietly disagreed with the number it claims to explain would
cost more trust than offering no drilldown at all.

No real database or dataset is touched: the connection is substituted and the
data is a small frame built in memory.
"""

import asyncio
import json
from datetime import datetime, timedelta

import httpx
import pandas as pd
import pytest
from httpx import ASGITransport

from app.main import app
from app.routers import share as share_router


# resolve_kpi_provenance reads business_terminology, so that is what a share
# has to carry for a drilldown to be possible at all.
SEMANTIC = {
    "business_terminology": {"primary_metric": "amount", "primary_metric_op": "sum"},
}


def _post(path: str, body: dict) -> httpx.Response:
    async def _call():
        async with httpx.AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            return await client.post(path, json=body)

    return asyncio.run(_call())


class _FakeCursor:
    def __init__(self, link, dataset):
        self._link, self._dataset = link, dataset
        self._result = None

    def execute(self, sql, params=None):
        s = " ".join(sql.split()).lower()
        if "from shared_links" in s:
            self._result = self._link
        elif "from datasets" in s:
            self._result = self._dataset
        else:
            self._result = None

    def fetchone(self):
        return self._result

    def fetchall(self):
        return []


class _FakeConn:
    def __init__(self, link, dataset):
        self._link, self._dataset = link, dataset

    def cursor(self):
        return _FakeCursor(self._link, self._dataset)

    def commit(self):
        pass

    def close(self):
        pass


@pytest.fixture
def wired(monkeypatch):
    """Returns a setter for the share link's state, so each test can describe
    the link it needs (expired, password-protected, missing) in one line."""
    state = {"link": None}

    def set_link(**overrides):
        link = {
            "dataset_id": "ds-1",
            "user_id": "owner-1",
            "password_hash": None,
            "expires_at": None,
        }
        link.update(overrides)
        state["link"] = link

    set_link()

    dataset = {"name": "sales.csv", "semantic_dict": json.dumps(SEMANTIC)}
    monkeypatch.setattr(
        share_router, "get_db_connection", lambda: _FakeConn(state["link"], dataset)
    )

    # Two rows contribute, one has no amount and must be excluded from both the
    # row list and the recomputed figure.
    df = pd.DataFrame({"amount": [100.0, 250.0, None], "region": ["N", "S", "E"]})
    monkeypatch.setattr(share_router, "get_dataframe", lambda ds, owner: df)

    return set_link


def test_returns_the_rows_and_a_figure_that_matches_them(wired):
    res = _post("/api/v1/share/tok/provenance", {"kpi_id": "kpi_rev"})
    assert res.status_code == 200

    body = res.json()
    assert body["rows_used"] == 2
    assert body["rows_total"] == 3
    assert body["excluded"] == 1
    assert "amount is empty" in body["excluded_reason"]
    # The whole point: this must equal what the card shows.
    assert body["recomputed_value"] == 350.0
    assert len(body["rows"]) == 2
    # The metric's own column leads, so the figure being explained is first.
    assert body["columns"][0] == "amount"


def test_a_password_protected_link_will_not_hand_over_rows(wired):
    wired(password_hash="$2b$12$abcdefghijklmnopqrstuv")

    res = _post("/api/v1/share/tok/provenance", {"kpi_id": "kpi_rev"})
    assert res.status_code == 401
    assert res.json()["detail"]["error"] == "password_required"


def test_a_wrong_password_is_refused(wired):
    from app.core.security import hash_password

    wired(password_hash=hash_password("correct-horse"))

    res = _post("/api/v1/share/tok/provenance", {"kpi_id": "kpi_rev", "password": "nope"})
    assert res.status_code == 401
    assert res.json()["detail"]["error"] == "incorrect_password"


def test_the_right_password_gets_through(wired):
    from app.core.security import hash_password

    wired(password_hash=hash_password("correct-horse"))

    res = _post(
        "/api/v1/share/tok/provenance", {"kpi_id": "kpi_rev", "password": "correct-horse"}
    )
    assert res.status_code == 200
    assert res.json()["recomputed_value"] == 350.0


def test_an_expired_link_is_refused(wired):
    wired(expires_at=(datetime.now() - timedelta(days=1)).isoformat())

    assert _post("/api/v1/share/tok/provenance", {"kpi_id": "kpi_rev"}).status_code == 410


def test_a_revoked_link_is_refused(wired, monkeypatch):
    # A revoked link is simply absent from the table. Patched through
    # monkeypatch so it is undone afterwards - assigning to the module
    # directly would leave every later test looking at a missing link and
    # passing for the wrong reason.
    monkeypatch.setattr(
        share_router, "get_db_connection", lambda: _FakeConn(None, {"name": "x", "semantic_dict": None})
    )
    assert _post("/api/v1/share/tok/provenance", {"kpi_id": "kpi_rev"}).status_code == 404


def test_an_unknown_metric_is_a_404_not_an_empty_table(wired):
    res = _post("/api/v1/share/tok/provenance", {"kpi_id": "kpi_not_a_thing"})
    assert res.status_code == 404


def test_kpi_id_is_required(wired):
    assert _post("/api/v1/share/tok/provenance", {}).status_code == 400
