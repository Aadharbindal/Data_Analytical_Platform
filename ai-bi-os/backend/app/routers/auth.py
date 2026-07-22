import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr
from app.core.database import get_db_connection
import uuid
from datetime import datetime

from app.core.config import DB_PATH
from app.core.security import (
    hash_password, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from slowapi import Limiter
from slowapi.util import get_remote_address

# Redis-backed when REDIS_HOST is set (matches app.worker's Celery broker
# config), so rate limits are shared correctly across multiple worker
# processes/instances instead of each one keeping its own in-memory count.
# in_memory_fallback_enabled means a missing/unreachable Redis degrades to
# per-process limiting rather than taking the whole app down.
_redis_host = os.getenv("REDIS_HOST")
_limiter_kwargs = {"key_func": get_remote_address}
if _redis_host:
    _limiter_kwargs["storage_uri"] = f"redis://{_redis_host}:{os.getenv('REDIS_PORT', '6379')}/{os.getenv('REDIS_RATELIMIT_DB', '1')}"
    _limiter_kwargs["in_memory_fallback_enabled"] = True

limiter = Limiter(**_limiter_kwargs)
router = APIRouter()

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    full_name: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def _create_session(cursor, user_id: str, request: Request) -> str:
    session_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO sessions (id, user_id, user_agent, ip_address, created_at, last_active_at, revoked) "
        "VALUES (%s, %s, %s, %s, %s, %s, 0)",
        (session_id, user_id, request.headers.get("user-agent", "Unknown device"), _client_ip(request), now, now),
    )
    return session_id

def _set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    secure_cookies = os.getenv("SECURE_COOKIES", "false").lower() == "true"
    samesite_mode = "none" if secure_cookies else "lax"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite=samesite_mode,
        secure=secure_cookies
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite=samesite_mode,
        secure=secure_cookies
    )

@router.post("/signup")
def signup(request: Request, user: UserSignup, response: Response):
    import re
    if len(user.password) < 8 or not re.search(r"[A-Za-z]", user.password) or not re.search(r"[0-9]", user.password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters and include a letter and a number.")

    conn = get_db_connection()
    cursor = conn.cursor()

    email_lower = user.email.lower()
    cursor.execute("SELECT id FROM users WHERE email=%s", (email_lower,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(user.password)
    now = datetime.utcnow().isoformat()

    cursor.execute(
        "INSERT INTO users (id, email, password_hash, full_name, created_at, is_active) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, email_lower, hashed_pw, user.full_name, now, 1)
    )
    session_id = _create_session(cursor, user_id, request)
    conn.commit()
    conn.close()

    access_token = create_access_token(user_id, session_id)
    refresh_token = create_refresh_token(user_id, session_id)
    _set_auth_cookies(response, access_token, refresh_token)

    return {"message": "User created successfully", "access_token": access_token, "token_type": "bearer"}

@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, user: UserLogin, response: Response):
    conn = get_db_connection()
    cursor = conn.cursor()

    email_lower = user.email.lower()
    cursor.execute("SELECT id, password_hash, is_active FROM users WHERE email=%s", (email_lower,))
    row = cursor.fetchone()

    if not row or not verify_password(user.password, row[1]):
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not row[2]:
        conn.close()
        raise HTTPException(status_code=401, detail="Account is inactive")

    user_id = row[0]
    session_id = _create_session(cursor, user_id, request)
    conn.commit()
    conn.close()

    access_token = create_access_token(user_id, session_id)
    refresh_token = create_refresh_token(user_id, session_id)
    _set_auth_cookies(response, access_token, refresh_token)

    return {"message": "Login successful", "access_token": access_token, "token_type": "bearer"}

@router.post("/refresh")
def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    import jwt
    from app.core.config import SECRET_KEY
    from app.core.security import ALGORITHM
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        session_id = payload.get("sid")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_active FROM users WHERE id=%s", (user_id,))
        row = cursor.fetchone()

        if not row or not row[0]:
            conn.close()
            raise HTTPException(status_code=401, detail="User inactive or not found")

        if session_id:
            cursor.execute("SELECT revoked FROM sessions WHERE id=%s AND user_id=%s", (session_id, user_id))
            srow = cursor.fetchone()
            if not srow or srow[0]:
                conn.close()
                raise HTTPException(status_code=401, detail="Session revoked")
            cursor.execute(
                "UPDATE sessions SET last_active_at=%s WHERE id=%s",
                (datetime.utcnow().isoformat(), session_id),
            )
            conn.commit()
        conn.close()

        access_token = create_access_token(user_id, session_id)
        secure_cookies = os.getenv("SECURE_COOKIES", "false").lower() == "true"
        samesite_mode = "none" if secure_cookies else "lax"

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite=samesite_mode,
            secure=secure_cookies
        )
        return {"message": "Token refreshed"}

    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/logout")
def logout(response: Response, current_user: dict = Depends(get_current_user)):
    if current_user.get("session_id"):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET revoked=1 WHERE id=%s", (current_user["session_id"],))
        conn.commit()
        conn.close()
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}

@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return current_user

@router.patch("/me")
def update_profile(update: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    full_name = update.full_name.strip()
    if not full_name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET full_name=%s WHERE id=%s", (full_name, current_user["id"]))
    conn.commit()
    conn.close()

    return {**current_user, "full_name": full_name}

@router.post("/change-password")
def change_password(body: PasswordChange, current_user: dict = Depends(get_current_user)):
    import re

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id=%s", (current_user["id"],))
    row = cursor.fetchone()

    # 403, not 401: this is a rejected business action by an already-authenticated
    # user (wrong current password), not an invalid/expired session — a 401 here
    # would make the frontend's global "session expired" handler log them out.
    if not row or not verify_password(body.current_password, row[0]):
        conn.close()
        raise HTTPException(status_code=403, detail="Current password is incorrect")

    if (
        len(body.new_password) < 8
        or not re.search(r"[A-Za-z]", body.new_password)
        or not re.search(r"[0-9]", body.new_password)
    ):
        conn.close()
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters and include a letter and a number.")

    cursor.execute(
        "UPDATE users SET password_hash=%s WHERE id=%s",
        (hash_password(body.new_password), current_user["id"]),
    )
    conn.commit()
    conn.close()

    return {"message": "Password updated successfully"}

@router.delete("/me")
def delete_account(response: Response, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    # Only rows actually scoped to this user get erased here — datasets,
    # regression models and the catalog are shared/global (no user_id column),
    # so account deletion doesn't touch data other users may depend on.
    for table in ("active_dataset", "knowledge_base", "insights", "ai_evaluation_logs", "recommendations", "rules", "sessions"):
        cursor.execute(f"DELETE FROM {table} WHERE user_id=%s", (user_id,))
    cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
    conn.commit()
    conn.close()

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Account deleted"}

def _parse_device(user_agent: str) -> str:
    ua = user_agent or ""
    if "Edg/" in ua:
        browser = "Edge"
    elif "Chrome/" in ua and "Chromium" not in ua:
        browser = "Chrome"
    elif "Firefox/" in ua:
        browser = "Firefox"
    elif "Safari/" in ua and "Chrome" not in ua:
        browser = "Safari"
    else:
        browser = "Unknown browser"

    if "Windows" in ua:
        os_name = "Windows"
    elif "Mac OS X" in ua or "Macintosh" in ua:
        os_name = "macOS"
    elif "Android" in ua:
        os_name = "Android"
    elif "iPhone" in ua or "iPad" in ua:
        os_name = "iOS"
    elif "Linux" in ua:
        os_name = "Linux"
    else:
        os_name = "Unknown OS"

    return f"{browser} on {os_name}"

@router.get("/sessions")
def list_sessions(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, user_agent, ip_address, created_at, last_active_at FROM sessions "
        "WHERE user_id=%s AND revoked=0 ORDER BY last_active_at DESC",
        (current_user["id"],),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "device": _parse_device(r[1]),
            "ip_address": r[2],
            "created_at": r[3],
            "last_active_at": r[4],
            "is_current": r[0] == current_user.get("session_id"),
        }
        for r in rows
    ]

@router.delete("/sessions/{session_id}")
def revoke_session(session_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sessions SET revoked=1 WHERE id=%s AND user_id=%s",
        (session_id, current_user["id"]),
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")
    conn.commit()
    conn.close()
    return {"message": "Session revoked"}

@router.delete("/sessions")
def revoke_other_sessions(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    current_sid = current_user.get("session_id")
    if current_sid:
        cursor.execute(
            "UPDATE sessions SET revoked=1 WHERE user_id=%s AND id != %s",
            (current_user["id"], current_sid),
        )
    else:
        cursor.execute("UPDATE sessions SET revoked=1 WHERE user_id=%s", (current_user["id"],))
    conn.commit()
    conn.close()
    return {"message": "Other sessions signed out"}

def _rules_rows(cursor, user_id: str):
    # "window" is a reserved word in Postgres — must stay quoted in the query.
    cursor.execute(
        'SELECT id, dataset_id, name, metric_column, condition, threshold, "window", is_active, created_at '
        "FROM rules WHERE user_id=%s",
        (user_id,),
    )
    return cursor.fetchall()

@router.get("/export-data")
def export_data(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = current_user["id"]

    def rows_for(table, columns):
        cursor.execute(f"SELECT {', '.join(columns)} FROM {table} WHERE user_id=%s", (user_id,))
        return [dict(zip(columns, r)) for r in cursor.fetchall()]

    export = {
        "exported_at": datetime.utcnow().isoformat(),
        "profile": {
            "id": current_user["id"],
            "email": current_user["email"],
            "full_name": current_user["full_name"],
            "member_since": current_user["created_at"],
        },
        "insights": rows_for("insights", [
            "id", "dataset_id", "title", "description", "category", "insight_level",
            "confidence", "impact", "recommendation", "verified", "created_at",
        ]),
        "recommendations": rows_for("recommendations", [
            "id", "dataset_id", "title", "rationale", "priority", "category", "verified", "created_at",
        ]),
        "rules": [
            dict(zip(
                ["id", "dataset_id", "name", "metric_column", "condition", "threshold", "window", "is_active", "created_at"],
                r,
            ))
            for r in _rules_rows(cursor, user_id)
        ],
        "knowledge_base_entries": rows_for("knowledge_base", ["id", "content", "doc_id", "chunk_index"]),
    }
    conn.close()
    return export
