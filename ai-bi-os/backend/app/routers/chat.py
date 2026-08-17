import json
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

from app.core.database import get_db_connection
from app.core.security import get_current_user
from app.services.data_processing import get_active_dataset, get_dataset_path
from app.services.query.duckdb_engine import DuckDBEngine
from app.ai.agents import AgentOrchestrator
from app.ai.governance import AIEvaluationFramework

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatFeedbackRequest(BaseModel):
    trace_id: str
    score: int
    comments: str = None


def _default_title(message: str, max_len: int = 60) -> str:
    title = " ".join(message.strip().split())
    return title[:max_len] + ("…" if len(title) > max_len else "")


def _row_to_session(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "is_pinned": bool(row["is_pinned"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "message_count": row["message_count"],
    }


def _row_to_message(row) -> dict:
    return {
        "id": row["id"],
        "role": row["role"],
        "content": row["content"],
        "executed_sql": row["executed_sql"],
        "chart_config": row["chart_config"],
        "trace_id": row["trace_id"],
        "created_at": row["created_at"],
    }


@router.get("/sessions")
async def list_sessions(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.id, s.title, s.is_pinned, s.created_at, s.updated_at,
               COUNT(m.id) AS message_count
        FROM chat_sessions s
        LEFT JOIN chat_messages m ON m.session_id = s.id
        WHERE s.user_id = %s
        GROUP BY s.id, s.title, s.is_pinned, s.created_at, s.updated_at
        ORDER BY s.is_pinned DESC, s.updated_at DESC
        """,
        (current_user["id"],),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_session(r) for r in rows]


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chat_sessions WHERE id = %s AND user_id = %s", (session_id, current_user["id"]))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")

    cursor.execute(
        """
        SELECT id, role, content, executed_sql, chart_config, trace_id, created_at
        FROM chat_messages WHERE session_id = %s ORDER BY created_at ASC
        """,
        (session_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_message(r) for r in rows]


# Only a read may be replayed. The SQL being re-run was written by the model,
# and although it already ran once when the answer was produced, "it ran before"
# is not a reason to run anything again unchecked. Anything that is not a plain
# SELECT or a CTE ending in one is refused rather than sanitised, because a
# rewrite that is nearly right is worse than a refusal.
_READ_ONLY_PREFIXES = ("select", "with")
_FORBIDDEN_SQL = (
    "insert", "update", "delete", "drop", "alter", "create", "attach",
    "copy", "export", "install", "load", "pragma", "call", "truncate",
)


def _is_read_only(sql: str) -> bool:
    stripped = " ".join((sql or "").strip().lower().split())
    if not stripped.startswith(_READ_ONLY_PREFIXES):
        return False
    # A statement separator means there is more than one statement, and only the
    # first was inspected. Trailing semicolons are fine.
    if ";" in stripped.rstrip(";"):
        return False
    return not any(f" {word} " in f" {stripped} " for word in _FORBIDDEN_SQL)


@router.get("/messages/{message_id}/provenance")
async def get_message_provenance(
    message_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """The queries behind one AI answer, re-run, with the rows they return.

    A figure the assistant states in prose is exactly the kind a reader cannot
    check, which is the reason this exists: the same promise the dashboard
    drilldown makes, kept in the one place the number arrives with the least
    evidence attached. The SQL is re-executed rather than replayed from a cached
    result, so what is shown is what the data says now, not what it said when
    the answer was written - and if those differ, that is worth seeing.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # Scoped by user_id, not just message id: a message id is guessable and
    # would otherwise expose another account's queries and rows.
    cursor.execute(
        "SELECT id, role, executed_sql, created_at FROM chat_messages WHERE id = %s AND user_id = %s",
        (message_id, current_user["id"]),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Message not found")

    raw = row["executed_sql"]
    statements = raw if isinstance(raw, list) else (json.loads(raw) if raw else [])
    if not statements:
        raise HTTPException(
            status_code=404,
            detail="This answer was not computed from your data, so there is nothing to show.",
        )

    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")

    filename_db = dataset_info.get("filepath")
    filepath = get_dataset_path(filename_db) if filename_db else None
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=400, detail="Dataset file is no longer available")

    fmt = "csv"
    if filepath.endswith(".parquet"):
        fmt = "parquet"
    elif filepath.endswith(".json"):
        fmt = "json"

    engine = DuckDBEngine()
    try:
        engine.register_dataset("active_dataset", filepath, format=fmt)

        capped = max(1, min(limit, 200))
        queries = []
        for sql in statements:
            if not _is_read_only(sql):
                queries.append({
                    "sql": sql,
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "truncated": False,
                    "error": "Refused: only read queries are re-run here.",
                })
                continue
            try:
                result = engine.execute(sql)
                rows = result.get("rows", [])
                queries.append({
                    "sql": sql,
                    "columns": [c["name"] for c in result.get("schema", [])],
                    "rows": rows[:capped],
                    "row_count": len(rows),
                    "truncated": len(rows) > capped,
                    "error": None,
                })
            except HTTPException as exc:
                # The engine raises HTTPException on a bad query. One statement
                # failing should not lose the others, so it is reported in place.
                queries.append({
                    "sql": sql,
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "truncated": False,
                    "error": str(exc.detail),
                })
    finally:
        engine.close()

    return {
        "message_id": message_id,
        "dataset_name": dataset_info.get("name") or dataset_info.get("filename"),
        "answered_at": row["created_at"],
        "queries": queries,
        "replayed_at": datetime.utcnow().isoformat() + "Z",
    }


@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chat_sessions WHERE id = %s AND user_id = %s", (session_id, current_user["id"]))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")

    update_fields = []
    params = []
    if "title" in data:
        update_fields.append("title = %s")
        params.append(data["title"])
    if "is_pinned" in data:
        update_fields.append("is_pinned = %s")
        params.append(1 if data["is_pinned"] else 0)

    if update_fields:
        query = f"UPDATE chat_sessions SET {', '.join(update_fields)} WHERE id = %s AND user_id = %s"
        params.extend([session_id, current_user["id"]])
        cursor.execute(query, tuple(params))
        conn.commit()

    conn.close()
    return {"success": True}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE session_id = %s AND user_id = %s", (session_id, current_user["id"]))
    cursor.execute("DELETE FROM chat_sessions WHERE id = %s AND user_id = %s", (session_id, current_user["id"]))
    conn.commit()
    conn.close()
    return {"success": True}


@router.post("")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()
    session_id = request.session_id
    is_new_session = False

    if session_id:
        cursor.execute("SELECT id FROM chat_sessions WHERE id = %s AND user_id = %s", (session_id, user_id))
        if not cursor.fetchone():
            session_id = None  # stale/foreign id — fall through and start a fresh session

    if not session_id:
        session_id = f"chatsess_{uuid.uuid4().hex[:8]}"
        cursor.execute(
            """
            INSERT INTO chat_sessions (id, user_id, title, is_pinned, created_at, updated_at)
            VALUES (%s, %s, %s, 0, %s, %s)
            """,
            (session_id, user_id, _default_title(request.message), now, now),
        )
        is_new_session = True
    else:
        cursor.execute("UPDATE chat_sessions SET updated_at = %s WHERE id = %s", (now, session_id))
    conn.commit()

    def save_message(role, content, executed_sql=None, chart_config=None, trace_id=None):
        """Returns the id it wrote, so the answer can be handed back with a
        handle the caller can use to ask how it was computed. Without it a
        freshly received answer is the one thing on screen that cannot be
        checked, which is exactly backwards."""
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        cursor.execute(
            """
            INSERT INTO chat_messages (id, session_id, user_id, role, content, executed_sql, chart_config, trace_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                message_id,
                session_id,
                user_id,
                role,
                content,
                json.dumps(executed_sql) if executed_sql is not None else None,
                json.dumps(chart_config) if chart_config is not None else None,
                trace_id,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return message_id

    save_message("user", request.message)

    def finish(response_text, executed_sql=None, chart_config=None, trace_id=None):
        message_id = save_message(
            "ai", response_text, executed_sql=executed_sql, chart_config=chart_config, trace_id=trace_id
        )
        conn.close()
        return {
            "response": response_text,
            "message_id": message_id,
            "executed_sql": executed_sql or [],
            "chart_config": chart_config,
            "trace_id": trace_id,
            "session_id": session_id,
            "is_new_session": is_new_session,
        }

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        return finish("AI features are not configured - add GROQ_API_KEY to your .env file.")

    dataset_info = get_active_dataset(user_id)
    if not dataset_info:
        return finish("No dataset uploaded yet.")

    filename_db = dataset_info.get("filepath")
    filepath = get_dataset_path(filename_db) if filename_db else None
    if not filepath or not os.path.exists(filepath):
        return finish("Failed to load data.")

    fmt = "csv"
    if filepath.endswith(".parquet"):
        fmt = "parquet"
    elif filepath.endswith(".json"):
        fmt = "json"

    try:
        engine = DuckDBEngine()
        engine.register_dataset("active_dataset", filepath, format=fmt)

        orchestrator = AgentOrchestrator()
        result = orchestrator.run_query(request.message, user_id=user_id, db_engine=engine)

        response_text = result.get("final_insight")
        executed_sql = result.get("executed_sql", [])
        trace_id = result.get("trace_id")

        # The agent sometimes wraps its answer as a JSON envelope carrying a
        # chart alongside the text — unwrap it here (once, server-side) so
        # what gets persisted is already the clean text + structured chart,
        # instead of every reader having to re-parse the raw response.
        chart_config = None
        try:
            clean = (response_text or "").replace("```json", "").replace("```", "").strip()
            if clean.startswith("{") and clean.endswith("}"):
                parsed = json.loads(clean)
                if "text_response" in parsed:
                    response_text = parsed["text_response"]
                    chart_config = parsed.get("chart_config")
        except Exception:
            pass

        return finish(response_text, executed_sql=executed_sql, chart_config=chart_config, trace_id=trace_id)
    except Exception as e:
        return finish(f"Error executing query: {str(e)}")


@router.post("/feedback")
async def submit_chat_feedback(request: ChatFeedbackRequest, current_user: dict = Depends(get_current_user)):
    """Records human feedback (thumbs up/down, a 1-5 score, etc.) against a
    previously logged AI response, identified by the trace_id returned from
    POST /api/v1/chat."""
    if not (1 <= request.score <= 5):
        raise HTTPException(status_code=400, detail="score must be between 1 and 5")

    updated = AIEvaluationFramework().submit_human_feedback(request.trace_id, request.score, request.comments)
    if not updated:
        raise HTTPException(status_code=404, detail="No logged AI response found for that trace_id")

    return {"status": "ok"}
