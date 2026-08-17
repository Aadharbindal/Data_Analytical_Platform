"""Tests that an uploaded dataset is still there tomorrow.

These exist because of a real failure. The host's filesystem is erased on every
restart and every deploy. A dataset's row lived in Postgres and survived, so its
name kept appearing in the picker - but the file behind it was gone, and every
figure computed from it came back as zero. The dashboard did not report an
error; it reported a revenue of 0.

So two things are asserted here. That the file itself is now kept somewhere
that survives a restart, and that when a file genuinely cannot be found the app
says so instead of answering with a confident zero.

The fake below is a real SQLite database rather than a mock, so the actual SQL
in file_store is executed - only the dialect is translated. A mock would happily
accept SQL that Postgres would reject.
"""

import os
import re
import sqlite3

import pytest

from app.services import file_store


# ── a real database, in the wrong dialect ────────────────────────────────────

def _to_sqlite(sql: str) -> str:
    sql = sql.replace("%s", "?")
    sql = re.sub(r"\bBYTEA\b", "BLOB", sql)
    sql = re.sub(r"\bTIMESTAMPTZ\b", "TEXT", sql)
    sql = re.sub(r"\bnow\(\)", "CURRENT_TIMESTAMP", sql)
    return sql


class _Cursor:
    def __init__(self, cur):
        self._cur = cur

    def execute(self, sql, params=()):
        return self._cur.execute(_to_sqlite(sql), params)

    def fetchone(self):
        return self._cur.fetchone()


class _Conn:
    """Quacks like PostgresConnectionProxy, backed by SQLite."""

    def __init__(self, db):
        self._db = db
        self.closed = False

    def cursor(self):
        return _Cursor(self._db.cursor())

    def commit(self):
        self._db.commit()

    def rollback(self):
        self._db.rollback()

    def close(self):
        # The real proxy returns the connection to a pool. Closing the shared
        # in-memory database here would throw the test's data away, so record
        # the call instead - leak-checking is what the assertions want anyway.
        self.closed = True


@pytest.fixture
def store(monkeypatch):
    db = sqlite3.connect(":memory:")
    opened = []

    def _connect():
        conn = _Conn(db)
        opened.append(conn)
        return conn

    monkeypatch.setattr(file_store, "get_db_connection", _connect)
    file_store.init_file_store()
    yield opened
    db.close()


# ── the file survives ────────────────────────────────────────────────────────

def test_a_saved_file_comes_back_byte_for_byte(store):
    # Real uploads are not text: an .xlsx is a zip, and a CSV can carry any
    # encoding. Anything that mangles bytes would corrupt the dataset silently.
    content = b"date,amount\n2026-01-01,1200\n\x00\xff\xfe binary tail"
    assert file_store.save("ds-1_bank.csv", content) is True
    assert file_store.load("ds-1_bank.csv") == content


def test_a_large_file_survives_the_round_trip(store):
    # MAX_UPLOAD_MB defaults to 50; a few MB is enough to catch a driver that
    # truncates or a column that was declared too narrow.
    content = (b"x" * 1024) * 1024 * 3  # 3MB
    assert file_store.save("big.csv", content) is True
    assert file_store.load("big.csv") == content


def test_re_uploading_the_same_name_replaces_it(store):
    file_store.save("ds-1_bank.csv", b"first")
    file_store.save("ds-1_bank.csv", b"second")
    # A retry after a half-finished upload must not collide on the primary key.
    assert file_store.load("ds-1_bank.csv") == b"second"


def test_a_file_that_was_never_saved_reads_as_missing(store):
    assert file_store.load("never-uploaded.csv") is None
    assert file_store.exists("never-uploaded.csv") is False


def test_deleting_removes_it_for_good(store):
    file_store.save("ds-1_bank.csv", b"data")
    assert file_store.exists("ds-1_bank.csv") is True

    assert file_store.delete("ds-1_bank.csv") is True
    assert file_store.exists("ds-1_bank.csv") is False
    # Otherwise the next read would restore the file the user just deleted.
    assert file_store.load("ds-1_bank.csv") is None


def test_deleting_something_absent_is_not_a_failure(store):
    assert file_store.delete("never-uploaded.csv") is True


def test_files_do_not_collide_with_each_other(store):
    file_store.save("a.csv", b"aaa")
    file_store.save("b.csv", b"bbb")
    assert file_store.load("a.csv") == b"aaa"
    assert file_store.load("b.csv") == b"bbb"


# ── putting the file back on disk ────────────────────────────────────────────

def test_a_wiped_file_is_restored_to_disk(store, tmp_path):
    content = b"date,amount\n2026-01-01,1200\n"
    file_store.save("ds-1_bank.csv", content)

    # Exactly what a redeploy leaves behind: the row, and no file.
    target = tmp_path / "ds-1_bank.csv"
    assert not target.exists()

    assert file_store.restore_to("ds-1_bank.csv", str(target)) is True
    assert target.read_bytes() == content


def test_restoring_a_file_that_was_never_stored_reports_failure(store, tmp_path):
    target = tmp_path / "never-uploaded.csv"
    assert file_store.restore_to("never-uploaded.csv", str(target)) is False
    # No empty file left behind, or the caller would read it as a valid dataset
    # with zero rows - which is the confident-zero bug all over again.
    assert not target.exists()


def test_a_restore_leaves_no_half_written_file(store, tmp_path, monkeypatch):
    monkeypatch.setattr(file_store, "capture", lambda *a, **k: None)
    file_store.save("ds-1_bank.csv", b"date,amount\n2026-01-01,1200\n")

    target = tmp_path / "ds-1_bank.csv"

    # A crash partway through the write. pandas would parse a truncated CSV
    # without complaint and every figure computed from it would be wrong, so
    # the real path must never hold a partial file.
    real_replace = os.replace
    monkeypatch.setattr(os, "replace", lambda *a: (_ for _ in ()).throw(OSError("no space")))

    assert file_store.restore_to("ds-1_bank.csv", str(target)) is False
    assert not target.exists()
    assert not (tmp_path / "ds-1_bank.csv.restoring").exists()
    monkeypatch.setattr(os, "replace", real_replace)


def test_a_restored_file_matches_the_original_exactly(store, tmp_path):
    # Binary formats go through this path too - an .xlsx is a zip archive.
    content = bytes(range(256)) * 40
    file_store.save("sheet.xlsx", content)
    target = tmp_path / "sheet.xlsx"

    assert file_store.restore_to("sheet.xlsx", str(target)) is True
    assert target.read_bytes() == content


# ── failures are reported, not swallowed ─────────────────────────────────────

def test_a_failed_save_is_reported_because_the_file_is_now_at_risk(monkeypatch):
    reported = []
    monkeypatch.setattr(file_store, "capture", lambda exc, **ctx: reported.append(ctx))

    class _Broken(_Conn):
        def cursor(self):
            raise Exception("connection refused")

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(file_store, "get_db_connection", lambda: _Broken(None))

    assert file_store.save("ds-1.csv", b"data") is False
    assert len(reported) == 1
    # The consequence is the part a reader needs: the upload looked fine.
    assert "ephemeral disk" in reported[0]["consequence"]
    assert reported[0]["filename"] == "ds-1.csv"


def test_a_failed_save_rolls_back_and_releases_the_connection(monkeypatch):
    monkeypatch.setattr(file_store, "capture", lambda *a, **k: None)
    events = []

    class _Failing(_Conn):
        def cursor(self):
            class _C:
                def execute(self, *a, **k):
                    raise Exception("disk full")
            return _C()

        def rollback(self):
            events.append("rollback")

        def close(self):
            events.append("close")

    monkeypatch.setattr(file_store, "get_db_connection", lambda: _Failing(None))
    file_store.save("ds-1.csv", b"data")

    # A connection left checked out on the error path exhausts the pool, which
    # turns one failed upload into an outage.
    assert events == ["rollback", "close"]


def test_a_read_failure_reads_as_missing_rather_than_crashing(monkeypatch):
    monkeypatch.setattr(file_store, "capture", lambda *a, **k: None)

    class _Broken(_Conn):
        def cursor(self):
            raise Exception("connection refused")

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(file_store, "get_db_connection", lambda: _Broken(None))
    # The caller can still fall through to object storage, and the "file is
    # gone" path tells the user the truth either way.
    assert file_store.load("ds-1.csv") is None


def test_every_call_releases_its_connection(store):
    file_store.save("a.csv", b"a")
    file_store.load("a.csv")
    file_store.exists("a.csv")
    file_store.delete("a.csv")

    assert all(conn.closed for conn in store)
    assert len(store) >= 4
