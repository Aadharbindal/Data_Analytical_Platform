"""Tests for the chat answer drilldown.

The endpoint re-runs SQL that a language model wrote, so the cases that matter
most here are the refusals: a non-read statement must not execute, and one
user must not be able to read another's queries by guessing a message id.

Nothing here touches a real database or a real dataset. The connection, the
active-dataset lookup and the current user are all substituted, and the data is
a temporary CSV written per test, so the suite is safe to run anywhere.
"""

import asyncio
import csv
import json
import os
import tempfile

import httpx
import pytest
from httpx import ASGITransport

from app.main import app
from app.core.security import get_current_user
from app.routers import chat as chat_router


USER = {"id": "user-1", "email": "a@example.com"}
OTHER_USER_ID = "user-2"


def _get(path: str) -> httpx.Response:
    async def _call():
        async with httpx.AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            return await client.get(path)

    return asyncio.run(_call())


class _FakeCursor:
    """Returns the one message row the endpoint asks for, but only when the
    query's user_id matches — the same scoping the real query relies on."""

    def __init__(self, rows_by_id):
        self._rows_by_id = rows_by_id
        self._result = None

    def execute(self, sql, params=None):
        message_id, user_id = params
        row = self._rows_by_id.get(message_id)
        self._result = row if row and row["user_id"] == user_id else None

    def fetchone(self):
        return self._result


class _FakeConn:
    def __init__(self, rows_by_id):
        self._rows_by_id = rows_by_id

    def cursor(self):
        return _FakeCursor(self._rows_by_id)

    def close(self):
        pass


@pytest.fixture
def dataset_csv():
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["region", "amount"])
        w.writerow(["North", "100"])
        w.writerow(["South", "250"])
        w.writerow(["North", "50"])
    yield path
    os.unlink(path)


@pytest.fixture
def wired(monkeypatch, dataset_csv):
    """Wires the endpoint to a fake message store and a temporary dataset."""
    rows = {}

    def add_message(message_id, sql_list, user_id=USER["id"]):
        rows[message_id] = {
            "id": message_id,
            "user_id": user_id,
            "role": "ai",
            "executed_sql": json.dumps(sql_list) if sql_list is not None else None,
            "created_at": "2026-01-01T00:00:00",
        }

    monkeypatch.setattr(chat_router, "get_db_connection", lambda: _FakeConn(rows))
    monkeypatch.setattr(
        chat_router, "get_active_dataset", lambda uid: {"id": "ds-1", "name": "sales.csv", "filepath": "sales.csv"}
    )
    monkeypatch.setattr(chat_router, "get_dataset_path", lambda name: dataset_csv)
    app.dependency_overrides[get_current_user] = lambda: USER

    yield add_message

    app.dependency_overrides.clear()


def test_replays_the_query_and_returns_its_rows(wired):
    wired("m1", ["SELECT region, amount FROM active_dataset ORDER BY amount"])

    res = _get("/api/v1/chat/messages/m1/provenance")
    assert res.status_code == 200

    body = res.json()
    assert len(body["queries"]) == 1
    q = body["queries"][0]
    assert q["error"] is None
    assert q["columns"] == ["region", "amount"]
    assert q["row_count"] == 3
    assert q["rows"][0]["amount"] == 50
    assert body["dataset_name"] == "sales.csv"


def test_aggregate_can_be_checked_against_the_stated_figure(wired):
    wired("m2", ["SELECT SUM(amount) AS total FROM active_dataset"])

    body = _get("/api/v1/chat/messages/m2/provenance").json()
    assert body["queries"][0]["rows"][0]["total"] == 400


def test_refuses_to_run_anything_that_is_not_a_read(wired):
    wired("m3", ["DELETE FROM active_dataset"])

    q = _get("/api/v1/chat/messages/m3/provenance").json()["queries"][0]
    assert q["error"] is not None
    assert q["rows"] == []


def test_refuses_a_read_with_a_second_statement_hidden_behind_it(wired):
    wired("m4", ["SELECT 1; DROP TABLE active_dataset"])

    q = _get("/api/v1/chat/messages/m4/provenance").json()["queries"][0]
    assert q["error"] is not None


def test_one_bad_statement_does_not_lose_the_others(wired):
    wired("m5", ["SELECT region FROM active_dataset", "SELECT * FROM no_such_table"])

    queries = _get("/api/v1/chat/messages/m5/provenance").json()["queries"]
    assert queries[0]["error"] is None and queries[0]["row_count"] == 3
    assert queries[1]["error"] is not None


def test_another_users_message_is_not_readable(wired):
    wired("m6", ["SELECT * FROM active_dataset"], user_id=OTHER_USER_ID)

    assert _get("/api/v1/chat/messages/m6/provenance").status_code == 404


def test_an_answer_with_no_sql_says_so_rather_than_returning_nothing(wired):
    wired("m7", [])

    res = _get("/api/v1/chat/messages/m7/provenance")
    assert res.status_code == 404
    assert "not computed from your data" in res.json()["detail"]


def test_rows_are_capped_and_the_cap_is_reported(wired):
    wired("m8", ["SELECT * FROM active_dataset"])

    body = _get("/api/v1/chat/messages/m8/provenance?limit=1").json()
    q = body["queries"][0]
    assert len(q["rows"]) == 1
    assert q["row_count"] == 3
    assert q["truncated"] is True
