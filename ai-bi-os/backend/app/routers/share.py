import json
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Body

from app.core.database import get_db_connection
from app.core.security import get_current_user, hash_password, verify_password
from app.routers.auth import limiter
from app.services.data_processing import get_active_dataset, get_dataframe
from app.services.stats_service import compute_kpis

router = APIRouter()


@router.post("/create")
async def create_share_link(
    data: dict = Body(default={}),
    current_user: dict = Depends(get_current_user),
):
    """Creates (or updates the protection settings of) the share link for the
    user's active dataset. Reuses the same token across calls so re-opening
    the share dialog and changing the password/expiry doesn't churn out a
    new URL every time — recipients who already have the link keep it valid
    (or invalid, if it just expired/got password-protected) rather than
    silently pointing at a dead one.

    A plain call with no body (the "open the dialog, give me the link" case)
    must NOT touch existing protection settings — only an explicit
    password/expires_in_hours key in the body updates them. Otherwise simply
    reopening the share dialog on an already-protected link would silently
    strip its password and expiry on every open.
    """
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset to share")

    update_password = "password" in data
    update_expiry = "expires_in_hours" in data

    password = data.get("password") or None
    if password is not None and len(password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters.")
    expires_in_hours = data.get("expires_in_hours")
    expires_at = None
    if expires_in_hours is not None:
        try:
            hours = float(expires_in_hours)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid expiry value.")
        if hours <= 0:
            raise HTTPException(status_code=400, detail="Invalid expiry value.")
        expires_at = (datetime.now() + timedelta(hours=hours)).isoformat()

    password_hash = hash_password(password) if password else None

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT token, created_at, view_count, password_hash, expires_at FROM shared_links WHERE user_id=%s AND dataset_id=%s",
        (current_user["id"], dataset_info["id"])
    )
    existing = cursor.fetchone()
    if existing:
        final_password_hash = password_hash if update_password else existing["password_hash"]
        final_expires_at = expires_at if update_expiry else existing["expires_at"]
        cursor.execute(
            "UPDATE shared_links SET password_hash=%s, expires_at=%s WHERE token=%s",
            (final_password_hash, final_expires_at, existing["token"])
        )
        conn.commit()
        conn.close()
        return {
            "token": existing["token"],
            "created_at": existing["created_at"],
            "view_count": existing["view_count"],
            "has_password": bool(final_password_hash),
            "expires_at": final_expires_at,
        }

    token = secrets.token_urlsafe(16)
    created_at = datetime.now().isoformat()
    cursor.execute(
        '''INSERT INTO shared_links (token, dataset_id, user_id, created_at, view_count, password_hash, expires_at)
           VALUES (%s, %s, %s, %s, 0, %s, %s)''',
        (token, dataset_info["id"], current_user["id"], created_at, password_hash, expires_at)
    )
    conn.commit()
    conn.close()
    return {
        "token": token,
        "created_at": created_at,
        "view_count": 0,
        "has_password": bool(password_hash),
        "expires_at": expires_at,
    }


@router.get("/mine")
async def list_my_share_links(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sl.token, sl.dataset_id, d.name, sl.created_at, sl.view_count, sl.last_viewed_at,
               sl.password_hash, sl.expires_at
        FROM shared_links sl
        JOIN datasets d ON d.id = sl.dataset_id
        WHERE sl.user_id = %s
        ORDER BY sl.created_at DESC
    ''', (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "token": r["token"],
            "dataset_id": r["dataset_id"],
            "dataset_name": r["name"],
            "created_at": r["created_at"],
            "view_count": r["view_count"],
            "last_viewed_at": r["last_viewed_at"],
            "has_password": bool(r["password_hash"]),
            "expires_at": r["expires_at"],
        }
        for r in rows
    ]


@router.delete("/{token}")
async def revoke_share_link(token: str, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shared_links WHERE token=%s AND user_id=%s", (token, current_user["id"]))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if not deleted:
        raise HTTPException(status_code=404, detail="Share link not found")
    return {"status": "revoked"}


@router.post("/{token}/data")
@limiter.limit("10/minute")
async def get_shared_dashboard_data(
    request: Request,
    token: str,
    data: dict = Body(default={}),
):
    """
    Public, unauthenticated: anyone holding the link (and the password, if
    one's set) can view a read-only snapshot of KPIs + verified insights.
    POST + body (not a query param) so a password never ends up in server
    logs, browser history, or a Referer header. Rate-limited per IP since
    this is the one endpoint in the app that accepts a password guess from
    an anonymous caller.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT dataset_id, user_id, password_hash, expires_at FROM shared_links WHERE token=%s",
        (token,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="This share link is invalid or has been revoked.")

    dataset_id, owner_id, password_hash, expires_at = (
        row["dataset_id"], row["user_id"], row["password_hash"], row["expires_at"]
    )

    if expires_at and datetime.now().isoformat() > expires_at:
        conn.close()
        raise HTTPException(status_code=410, detail="This share link has expired.")

    if password_hash:
        supplied = data.get("password")
        if not supplied:
            conn.close()
            raise HTTPException(status_code=401, detail={"error": "password_required"})
        if not verify_password(supplied, password_hash):
            conn.close()
            raise HTTPException(status_code=401, detail={"error": "incorrect_password"})

    cursor.execute(
        "UPDATE shared_links SET view_count = view_count + 1, last_viewed_at = %s WHERE token = %s",
        (datetime.now().isoformat(), token)
    )

    cursor.execute("SELECT name, semantic_dict FROM datasets WHERE id=%s AND user_id=%s", (dataset_id, owner_id))
    ds_row = cursor.fetchone()
    if not ds_row:
        conn.commit()
        conn.close()
        raise HTTPException(status_code=404, detail="The shared dataset is no longer available.")
    dataset_name, semantic_dict_raw = ds_row["name"], ds_row["semantic_dict"]
    semantic_dict = None
    if semantic_dict_raw:
        semantic_dict = semantic_dict_raw if isinstance(semantic_dict_raw, (dict, list)) else json.loads(semantic_dict_raw)

    cursor.execute('''
        SELECT title, description, impact, confidence, category
        FROM insights
        WHERE user_id=%s AND dataset_id=%s AND verified=1
        ORDER BY created_at DESC
        LIMIT 6
    ''', (owner_id, dataset_id))
    insight_rows = cursor.fetchall()
    conn.commit()
    conn.close()

    df = get_dataframe(dataset_id, owner_id)
    if df is None:
        raise HTTPException(status_code=404, detail="The shared dataset is no longer available.")

    kpi_data = compute_kpis(df, semantic_dict)

    insights = [
        {"title": r["title"], "description": r["description"], "impact": r["impact"],
         "confidence": r["confidence"], "category": r["category"]}
        for r in insight_rows
    ]

    return {
        "dataset_name": dataset_name,
        "row_count": len(df),
        "kpis": kpi_data.get("kpis", []),
        "chart_data": kpi_data.get("chart_data", []),
        "insights": insights,
    }
