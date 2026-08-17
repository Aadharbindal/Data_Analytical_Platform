"""Tests that storage failures are noticed.

These exist because of a real one. Object storage had been unreachable for
months: every upload failed, fell back to local disk, printed a line into a log
stream nobody reads, and the host wiped that disk on the next deploy. The
datasets were gone and nothing said so until a shared dashboard could not find
its own data.

So what is asserted here is not that uploads work - it is that when they do
not, somebody is told.
"""

from app.services import storage as st


class _BrokenClient:
    """Fails whatever it is asked, the way a wrong endpoint or key does."""

    def __init__(self, exc=None):
        self._exc = exc or Exception("An error occurred (540) when calling the operation")

    def put_object(self, **kw):
        raise self._exc

    def download_file(self, *a, **kw):
        raise self._exc

    def delete_object(self, **kw):
        raise self._exc

    def get_object(self, **kw):
        raise self._exc

    def head_bucket(self, **kw):
        raise self._exc


def _manager(monkeypatch, client=None, enabled=True):
    m = st.S3StorageManager()
    m.enabled = enabled
    m.s3_client = client
    m.bucket_name = "backend-key"
    m.endpoint_url = "https://example.storage.supabase.co/storage/v1/s3"
    return m


# ── every failing operation gets reported ────────────────────────────────────

def test_a_failed_upload_is_reported_not_printed(monkeypatch):
    reported = []
    monkeypatch.setattr(st, "capture", lambda exc, **ctx: reported.append(ctx))

    m = _manager(monkeypatch, _BrokenClient())
    assert m.upload_file(b"data", "f.csv") is False

    assert len(reported) == 1
    assert reported[0]["action"] == "upload"
    assert reported[0]["bucket"] == "backend-key"
    # The consequence is the part a reader needs: the file is not safe.
    assert "local disk" in reported[0]["consequence"]


def test_download_delete_and_read_failures_are_reported(monkeypatch):
    reported = []
    monkeypatch.setattr(st, "capture", lambda exc, **ctx: reported.append(ctx["action"]))

    m = _manager(monkeypatch, _BrokenClient())
    m.download_file("f.csv", "/tmp/f.csv")
    m.delete_file("f.csv")
    m.get_file_bytes("f.csv")

    assert reported == ["download", "delete", "read"]


def test_credentials_are_never_in_the_report(monkeypatch):
    reported = []
    monkeypatch.setattr(st, "capture", lambda exc, **ctx: reported.append(ctx))

    m = _manager(monkeypatch, _BrokenClient())
    m.aws_secret_access_key = "super-secret-value"
    m.upload_file(b"x", "f.csv")

    assert "super-secret-value" not in str(reported)


# ── the startup check ────────────────────────────────────────────────────────

def test_a_working_bucket_reports_ok(monkeypatch):
    class _Fine:
        def head_bucket(self, **kw):
            return {}

    monkeypatch.setattr(st, "s3_manager", _manager(monkeypatch, _Fine()))
    assert st.report_storage_status() is True


def test_configured_but_unreachable_is_raised_loudly(monkeypatch):
    messages = []
    monkeypatch.setattr(st, "capture_message", lambda msg, **kw: messages.append((msg, kw)))
    monkeypatch.setattr(st, "s3_manager", _manager(monkeypatch, _BrokenClient()))

    assert st.report_storage_status() is False

    # This is the exact situation that went unnoticed: someone asked for
    # persistence and is not getting it.
    assert len(messages) == 1
    msg, kw = messages[0]
    assert "will not survive" in msg
    assert kw["bucket"] == "backend-key"


def test_storage_switched_off_is_a_warning_not_an_alert(monkeypatch):
    messages = []
    monkeypatch.setattr(st, "capture_message", lambda msg, **kw: messages.append(msg))
    monkeypatch.setattr(st, "s3_manager", _manager(monkeypatch, None, enabled=False))

    # Running without object storage is a legitimate local setup. Reporting it
    # as an incident would train people to ignore the alert that matters.
    assert st.report_storage_status() is False
    assert messages == []


def test_check_connection_explains_which_bucket_and_where(monkeypatch):
    m = _manager(monkeypatch, _BrokenClient())
    ok, detail = m.check_connection()
    assert ok is False
    assert "backend-key" in detail
    assert "supabase" in detail


def test_check_connection_without_credentials_names_the_missing_ones(monkeypatch):
    m = _manager(monkeypatch, None, enabled=False)
    ok, detail = m.check_connection()
    assert ok is False
    assert "AWS_ACCESS_KEY_ID" in detail
