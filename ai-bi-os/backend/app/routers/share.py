import json
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Body

from app.core.database import get_db_connection
from app.core.security import get_current_user, hash_password, verify_password
from app.routers.auth import limiter
from app.services.data_processing import get_active_dataset, get_dataframe
from app.services.stats_service import compute_kpis, resolve_kpi_provenance

router = APIRouter()


def _resolve_share(cursor, token: str, password: Optional[str]) -> tuple:
    """Validate a share token, its expiry and its password, returning the
    dataset and owner it points at.

    Shared by the dashboard and its drilldown so the two can never disagree
    about who is allowed in: a drilldown that checked the token but forgot the
    password would hand the underlying rows to anyone holding the link, which
    is a worse leak than the dashboard it sits behind.
    """
    cursor.execute(
        "SELECT dataset_id, user_id, password_hash, expires_at FROM shared_links WHERE token=%s",
        (token,),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="This share link is invalid or has been revoked.")

    if row["expires_at"] and datetime.now().isoformat() > row["expires_at"]:
        raise HTTPException(status_code=410, detail="This share link has expired.")

    if row["password_hash"]:
        if not password:
            raise HTTPException(status_code=401, detail={"error": "password_required"})
        if not verify_password(password, row["password_hash"]):
            raise HTTPException(status_code=401, detail={"error": "incorrect_password"})

    return row["dataset_id"], row["user_id"]


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
    try:
        dataset_id, owner_id = _resolve_share(cursor, token, data.get("password"))
    except HTTPException:
        conn.close()
        raise

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
        SELECT title, description, impact, confidence, category, dimension_type
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

    # Same formatting the private Insights page uses, so a viewer with the
    # link sees "1.4K Records" for the same insight the owner sees privately
    # -- not the raw number reinterpreted as currency by a client-side
    # formatter that has no way to know it's a row count.
    from app.routers.insights import format_insight_impact
    insights = [
        {"title": r["title"], "description": r["description"],
         "impact": format_insight_impact(r["impact"], r["title"], r["dimension_type"]),
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


@router.post("/{token}/provenance")
@limiter.limit("10/minute")
async def get_shared_kpi_provenance(
    request: Request,
    token: str,
    data: dict = Body(default={}),
):
    """The rows behind one figure on a shared dashboard, and that figure
    recomputed from exactly those rows.

    The person holding a share link is the one with the least reason to take a
    number on trust: they did not build the dashboard, cannot see the data, and
    in most cases do not have an account. Giving the owner a drilldown and the
    recipient none puts the check in the one place it is least needed.

    Same token, expiry and password gate as the dashboard itself, and the same
    per-IP limit, since this reads the underlying rows.
    """
    kpi_id = data.get("kpi_id")
    if not kpi_id:
        raise HTTPException(status_code=400, detail="kpi_id is required")

    limit = max(1, min(int(data.get("limit", 50)), 200))
    offset = max(0, int(data.get("offset", 0)))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        dataset_id, owner_id = _resolve_share(cursor, token, data.get("password"))
        cursor.execute(
            "SELECT name, semantic_dict FROM datasets WHERE id=%s AND user_id=%s",
            (dataset_id, owner_id),
        )
        ds_row = cursor.fetchone()
    finally:
        conn.close()

    if not ds_row:
        raise HTTPException(status_code=404, detail="The shared dataset is no longer available.")

    semantic_raw = ds_row["semantic_dict"]
    semantic_dict = None
    if semantic_raw:
        semantic_dict = semantic_raw if isinstance(semantic_raw, (dict, list)) else json.loads(semantic_raw)

    df = get_dataframe(dataset_id, owner_id)
    if df is None:
        raise HTTPException(status_code=404, detail="The shared dataset is no longer available.")

    prov = resolve_kpi_provenance(df, semantic_dict, kpi_id)
    if not prov:
        raise HTTPException(status_code=404, detail="No provenance for this metric")

    col, op, mask = prov["column"], prov["aggregation"], prov["mask"]
    used = df[mask]
    rows_used, rows_total = int(len(used)), int(len(df))

    # Recomputed from the contributing rows with the same aggregation
    # compute_kpis applied, so the viewer can hold it against the card.
    recomputed = None
    try:
        if op == "sum":
            recomputed = float(used[col].sum())
        elif op == "mean":
            recomputed = float(used[col].mean())
        elif op == "nunique":
            recomputed = float(used[col].nunique())
        elif op == "count":
            recomputed = float(rows_used)
        elif op == "percent":
            healthy = (semantic_dict or {}).get("business_terminology", {}).get("status_healthy_regex", "")
            s = used[col].astype(str)
            recomputed = (
                float(s.str.contains(healthy, case=False, na=False).sum() / len(used) * 100)
                if len(used)
                else 0.0
            )
    except Exception:
        recomputed = None

    if recomputed is not None:
        recomputed = round(recomputed, 1 if op == "percent" else 2)

    ordered = [col] + [c for c in df.columns if c != col]
    page = used.iloc[offset : offset + limit][ordered]
    records = json.loads(page.to_json(orient="records", date_format="iso"))

    excluded = rows_total - rows_used
    return {
        "kpi_id": kpi_id,
        "column": col,
        "aggregation": op,
        "formula": prov["formula"],
        "note": prov["note"],
        "rows_used": rows_used,
        "rows_total": rows_total,
        "excluded": excluded,
        "excluded_reason": (
            f"{excluded} row{'s' if excluded != 1 else ''} left out because {col} is empty"
            if excluded > 0
            else None
        ),
        "recomputed_value": recomputed,
        "columns": list(page.columns),
        "rows": records,
    }
