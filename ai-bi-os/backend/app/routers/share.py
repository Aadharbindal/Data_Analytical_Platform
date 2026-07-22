import json
import secrets
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends

from app.core.database import get_db_connection
from app.services.data_processing import get_active_dataset, get_dataframe
from app.services.stats_service import compute_kpis
from app.core.security import get_current_user

router = APIRouter()


@router.post("/create")
async def create_share_link(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset to share")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Reuse the existing link for this (user, dataset) pair instead of piling up duplicates
    cursor.execute(
        "SELECT token, created_at, view_count FROM shared_links WHERE user_id=%s AND dataset_id=%s",
        (current_user["id"], dataset_info["id"])
    )
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return {"token": existing[0], "created_at": existing[1], "view_count": existing[2]}

    token = secrets.token_urlsafe(16)
    created_at = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO shared_links (token, dataset_id, user_id, created_at, view_count) VALUES (%s, %s, %s, %s, 0)",
        (token, dataset_info["id"], current_user["id"], created_at)
    )
    conn.commit()
    conn.close()
    return {"token": token, "created_at": created_at, "view_count": 0}


@router.get("/mine")
async def list_my_share_links(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sl.token, sl.dataset_id, d.name, sl.created_at, sl.view_count, sl.last_viewed_at
        FROM shared_links sl
        JOIN datasets d ON d.id = sl.dataset_id
        WHERE sl.user_id = %s
        ORDER BY sl.created_at DESC
    ''', (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "token": r[0],
            "dataset_id": r[1],
            "dataset_name": r[2],
            "created_at": r[3],
            "view_count": r[4],
            "last_viewed_at": r[5],
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


@router.get("/{token}/data")
async def get_shared_dashboard_data(token: str):
    """
    Public, unauthenticated: anyone holding the link can view a read-only
    snapshot of KPIs + verified insights for the dataset it points to.
    No session, no cookie, no bearer token required by design.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT dataset_id, user_id FROM shared_links WHERE token=%s", (token,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="This share link is invalid or has been revoked.")

    dataset_id, owner_id = row

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
    dataset_name, semantic_dict_raw = ds_row
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
        {"title": r[0], "description": r[1], "impact": r[2], "confidence": r[3], "category": r[4]}
        for r in insight_rows
    ]

    return {
        "dataset_name": dataset_name,
        "row_count": len(df),
        "kpis": kpi_data.get("kpis", []),
        "chart_data": kpi_data.get("chart_data", []),
        "insights": insights,
    }
