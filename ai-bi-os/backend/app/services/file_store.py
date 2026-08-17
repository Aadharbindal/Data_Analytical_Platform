"""Durable storage for uploaded dataset files, kept in Postgres.

Why the database and not the disk: this host's filesystem is ephemeral. It is
wiped on every restart and every deploy. A dataset's *row* lived in Postgres and
survived, so the file name kept appearing in the picker long after the file
itself was gone - and every figure computed from it silently came back as zero.
The dashboard did not say "the data is missing", it said the revenue was 0.

Object storage was supposed to be the backstop, but it has to be configured
correctly to be one, and when it is not there is nothing to notice the gap.
Postgres is already a hard requirement for this app to run at all: if it is
reachable the files are reachable, and there is no second thing to keep working.

Files are capped by MAX_UPLOAD_MB (50MB by default), which bytea holds without
complaint. The local disk stays in front of this as a cache - reads still come
from a real file on a real path, so nothing downstream had to change.
"""

import logging
import os
from typing import Optional

from app.core.database import get_db_connection
from app.core.error_tracking import capture

logger = logging.getLogger(__name__)


def init_file_store() -> None:
    """Create the table. Safe to call on every boot."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS dataset_files (
                filename TEXT PRIMARY KEY,
                content BYTEA NOT NULL,
                size_bytes BIGINT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def save(filename: str, content: bytes) -> bool:
    """Store a file's bytes. Returns whether it is now safely persisted.

    Re-uploading the same name overwrites, so a retry after a half-finished
    upload leaves one row rather than failing on the primary key.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO dataset_files (filename, content, size_bytes)
            VALUES (%s, %s, %s)
            ON CONFLICT (filename)
            DO UPDATE SET content = EXCLUDED.content,
                          size_bytes = EXCLUDED.size_bytes,
                          created_at = now()
            """,
            (filename, memoryview(content), len(content)),
        )
        conn.commit()
        logger.info("Persisted %s (%d bytes) to the database", filename, len(content))
        return True
    except Exception as exc:
        conn.rollback()
        # The upload itself may still appear to succeed, so this has to be loud:
        # the file is now on ephemeral disk only, which is the exact situation
        # this module exists to end.
        logger.error("Could not persist %s to the database: %s", filename, exc)
        capture(
            exc,
            action="file_store.save",
            filename=filename,
            size_bytes=len(content),
            consequence="file exists only on ephemeral disk and will not survive a restart",
        )
        return False
    finally:
        conn.close()


def load(filename: str) -> Optional[bytes]:
    """Fetch a file's bytes, or None if it was never stored."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM dataset_files WHERE filename = %s", (filename,))
        row = cursor.fetchone()
        if not row or row[0] is None:
            return None
        return bytes(row[0])
    except Exception as exc:
        logger.error("Could not read %s from the database: %s", filename, exc)
        capture(exc, action="file_store.load", filename=filename)
        return None
    finally:
        conn.close()


def restore_to(filename: str, local_path: str) -> bool:
    """Put a stored file back on disk at `local_path`. Returns whether it is there.

    This is the step that undoes a wiped filesystem, so it runs on the read
    path of every dataset whose file went missing. It writes under a temporary
    name and moves the result into place, so a second request arriving mid
    restore either sees no file or sees the whole file - never a truncated one
    that pandas would happily parse into wrong numbers.
    """
    content = load(filename)
    if content is None:
        return False

    tmp_path = f"{local_path}.restoring"
    try:
        with open(tmp_path, "wb") as f:
            f.write(content)
        os.replace(tmp_path, local_path)
        logger.info("Restored %s from the database (%d bytes)", filename, len(content))
        return True
    except Exception as exc:
        logger.error("Could not write restored file %s to disk: %s", filename, exc)
        capture(exc, action="file_store.restore_to", filename=filename)
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        return False


def delete(filename: str) -> bool:
    """Forget a file. Deleting one that was never there is not a failure."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dataset_files WHERE filename = %s", (filename,))
        conn.commit()
        return True
    except Exception as exc:
        conn.rollback()
        logger.error("Could not delete %s from the database: %s", filename, exc)
        capture(exc, action="file_store.delete", filename=filename)
        return False
    finally:
        conn.close()


def exists(filename: str) -> bool:
    """Whether a file is durably stored, without pulling its bytes across."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM dataset_files WHERE filename = %s", (filename,))
        return cursor.fetchone() is not None
    except Exception as exc:
        logger.error("Could not check %s in the database: %s", filename, exc)
        capture(exc, action="file_store.exists", filename=filename)
        return False
    finally:
        conn.close()
