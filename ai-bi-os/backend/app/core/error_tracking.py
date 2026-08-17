"""Reporting for errors nobody is watching for.

Until now a 500 in production was visible only to whoever happened to hit it.
The user saw a generic failure, the server logged a traceback into a stream
nobody reads, and the first anyone heard of a broken endpoint was a complaint.

Everything here is optional. With no SENTRY_DSN set the app behaves exactly as
it did before - no dependency required at runtime, no network calls, no
behaviour change - so local development and anyone who would rather not send
data to a third party are unaffected.
"""

import logging
import os
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)

_enabled = False

# Anything whose name looks like one of these is replaced before a report
# leaves the building. An error report is a debugging aid, not a reason to hand
# a third party a password, a session token or somebody's rows.
_SENSITIVE_KEY = re.compile(
    r"password|passwd|secret|token|api[_-]?key|authorization|cookie|dsn|"
    r"credential|private|totp|salt|hash",
    re.IGNORECASE,
)

# Request bodies and query results carry the user's actual data. There is no
# version of "a sample of their spreadsheet" that belongs in an error tracker.
_DROP_ENTIRELY = {"data", "rows", "records", "df", "dataframe", "body", "payload"}

_REDACTED = "[redacted]"


def _scrub(value: Any, depth: int = 0) -> Any:
    """Walk a structure replacing anything sensitive.

    Depth-limited because Sentry hands us frame locals, which can contain
    deeply nested or self-referential objects; a scrubber that hangs while
    reporting an error is worse than the error.
    """
    if depth > 4:
        return _REDACTED
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            key = str(k)
            if _SENSITIVE_KEY.search(key):
                out[key] = _REDACTED
            elif key.lower() in _DROP_ENTIRELY:
                out[key] = _REDACTED
            else:
                out[key] = _scrub(v, depth + 1)
        return out
    if isinstance(value, (list, tuple)):
        return [_scrub(v, depth + 1) for v in value[:20]]
    return value


def _before_send(event: dict, hint: dict) -> Optional[dict]:
    try:
        if "request" in event:
            req = event["request"]
            req.pop("data", None)
            req.pop("cookies", None)
            if "headers" in req:
                req["headers"] = _scrub(req["headers"])
            # A query string can carry an id or a filter value; the path alone
            # is enough to find the endpoint that broke.
            req.pop("query_string", None)

        for exc in event.get("exception", {}).get("values", []):
            for frame in exc.get("stacktrace", {}).get("frames", []):
                if "vars" in frame:
                    frame["vars"] = _scrub(frame["vars"])

        if "extra" in event:
            event["extra"] = _scrub(event["extra"])
    except Exception:
        # A scrubber that raises would send the unscrubbed event or lose it
        # entirely. Dropping the report is the safe failure.
        return None
    return event


def init_error_tracking(app=None) -> bool:
    """Start reporting if a DSN is configured. Returns whether it did."""
    global _enabled

    dsn = (os.getenv("SENTRY_DSN") or "").strip()
    if not dsn:
        logger.info("Error tracking disabled: no SENTRY_DSN set.")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        # Configured but not installed is a mistake worth saying out loud,
        # rather than silently running without the reporting someone asked for.
        logger.warning("SENTRY_DSN is set but sentry-sdk is not installed; error tracking is off.")
        return False

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("ENVIRONMENT", "production"),
        release=os.getenv("RELEASE") or None,
        # Off by default. Personally identifiable information is opt-in, and
        # the scrubber above assumes it is not arriving.
        send_default_pii=False,
        # A fraction, not everything: performance traces on every request would
        # cost more than they teach on an app this size.
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.05")),
        before_send=_before_send,
        integrations=[StarletteIntegration(), FastApiIntegration()],
    )
    _enabled = True
    logger.info("Error tracking enabled.")
    return True


def capture(exc: BaseException, **context) -> None:
    """Report one exception. Silent when tracking is off."""
    if not _enabled:
        return
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in _scrub(context).items():
                scope.set_extra(key, value)
            sentry_sdk.capture_exception(exc)
    except Exception:
        logger.exception("Failed to report an exception")


def capture_message(message: str, level: str = "error", **context) -> None:
    """Report something that is wrong but did not raise - a browser crash
    forwarded from the client, for instance."""
    if not _enabled:
        return
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in _scrub(context).items():
                scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level=level)
    except Exception:
        logger.exception("Failed to report a message")


def is_enabled() -> bool:
    return _enabled
