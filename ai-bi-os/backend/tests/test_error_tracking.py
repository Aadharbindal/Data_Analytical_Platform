"""Tests for error reporting, and mostly for what it refuses to send.

An error tracker is a pipe out of the building. The interesting cases are not
whether a report arrives but whether a password, a session token or a row of
somebody's spreadsheet can ride along with it.
"""

import asyncio

import httpx
from httpx import ASGITransport

from app.core import error_tracking as et
from app.main import app


def _post(path: str, body: dict) -> httpx.Response:
    async def _call():
        async with httpx.AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            return await client.post(path, json=body)

    return asyncio.run(_call())


# ── what must never leave ────────────────────────────────────────────────────

def test_secrets_are_replaced_whatever_they_are_called():
    scrubbed = et._scrub({
        "password": "hunter2",
        "access_token": "eyJhbGciOi",
        "GROQ_API_KEY": "sk-live-1",
        "Authorization": "Bearer abc",
        "db_password_hash": "$2b$12$x",
        "totp_secret": "JBSWY3DP",
        "cookie": "session=1",
    })
    assert all(v == "[redacted]" for v in scrubbed.values()), scrubbed


def test_the_users_own_data_is_dropped_not_summarised():
    scrubbed = et._scrub({
        "rows": [{"salary": 90000, "name": "A Person"}],
        "data": {"anything": 1},
        "dataframe": "...",
    })
    assert scrubbed == {
        "rows": "[redacted]",
        "data": "[redacted]",
        "dataframe": "[redacted]",
    }


def test_ordinary_context_survives():
    # Scrubbing everything would make reports useless; the point is to keep
    # what identifies the fault.
    scrubbed = et._scrub({"path": "/api/v1/datasets", "status": 500, "dataset_id": "ds-1"})
    assert scrubbed == {"path": "/api/v1/datasets", "status": 500, "dataset_id": "ds-1"}


def test_nested_secrets_are_found():
    scrubbed = et._scrub({"config": {"db": {"password": "x", "host": "localhost"}}})
    assert scrubbed["config"]["db"]["password"] == "[redacted]"
    assert scrubbed["config"]["db"]["host"] == "localhost"


def test_deep_structures_stop_rather_than_recurse_forever():
    # Sentry hands over frame locals, which can be deeply nested or even
    # self-referential. What matters is that the walk terminates and that
    # anything past the limit is dropped rather than passed through.
    deep = {"a": {"b": {"c": {"d": {"e": {"f": "too far"}}}}}}
    assert et._scrub(deep)["a"]["b"]["c"]["d"]["e"] == "[redacted]"


def test_a_self_referential_structure_does_not_hang():
    loop: dict = {"name": "root"}
    loop["self"] = loop
    assert et._scrub(loop)["name"] == "root"


def test_long_lists_are_truncated():
    assert len(et._scrub({"items": list(range(500))})["items"]) == 20


def test_request_body_and_cookies_never_reach_the_event():
    event = {
        "request": {
            "url": "/api/v1/auth/login",
            "data": {"password": "hunter2"},
            "cookies": {"refresh_token": "abc"},
            "query_string": "token=secret",
            "headers": {"Authorization": "Bearer x", "User-Agent": "Firefox"},
        }
    }
    out = et._before_send(event, {})
    assert "data" not in out["request"]
    assert "cookies" not in out["request"]
    assert "query_string" not in out["request"]
    assert out["request"]["headers"]["Authorization"] == "[redacted]"
    assert out["request"]["headers"]["User-Agent"] == "Firefox"


def test_frame_locals_are_scrubbed():
    event = {
        "exception": {
            "values": [{"stacktrace": {"frames": [{"vars": {"password": "p", "n": 3}}]}}]
        }
    }
    frame = et._before_send(event, {})["exception"]["values"][0]["stacktrace"]["frames"][0]
    assert frame["vars"]["password"] == "[redacted]"
    assert frame["vars"]["n"] == 3


def test_a_scrubber_failure_drops_the_report_rather_than_sending_it_raw(monkeypatch):
    monkeypatch.setattr(et, "_scrub", lambda *a, **k: (_ for _ in ()).throw(ValueError("boom")))
    assert et._before_send({"extra": {"password": "leak"}}, {}) is None


# ── switching on and off ─────────────────────────────────────────────────────

def test_no_dsn_means_no_tracking(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    assert et.init_error_tracking() is False


def test_capture_is_silent_when_tracking_is_off(monkeypatch):
    monkeypatch.setattr(et, "_enabled", False)
    et.capture(ValueError("nobody is listening"))  # must not raise


# ── the browser's own channel ────────────────────────────────────────────────

def test_a_browser_crash_is_accepted():
    res = _post(
        "/api/v1/telemetry/browser-error",
        {"message": "Cannot read properties of undefined", "path": "/chat", "kind": "render"},
    )
    assert res.status_code == 204


def test_a_broken_page_is_not_given_a_second_error_to_handle():
    # Oversized fields are rejected by validation, but the page that sent them
    # has already crashed - so the check here is simply that nothing explodes.
    res = _post("/api/v1/telemetry/browser-error", {"message": "x" * 5000})
    assert res.status_code in (204, 422)


def test_the_report_endpoint_needs_no_session():
    # A crash on the sign-in page happens before anyone is logged in; requiring
    # auth would lose exactly the reports that matter most.
    res = _post("/api/v1/telemetry/browser-error", {"message": "crashed while signed out"})
    assert res.status_code == 204
