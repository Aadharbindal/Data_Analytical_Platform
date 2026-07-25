from datetime import datetime
import json

from fastapi import APIRouter, Body, Depends

from app.core.database import get_db_connection
from app.core.security import get_current_user

router = APIRouter()


@router.get("/layout")
async def get_dashboard_layout(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT pinned_kpis FROM dashboard_preferences WHERE user_id = %s",
        (current_user["id"],),
    )
    row = cursor.fetchone()
    conn.close()
    pinned = row[0] if row and row[0] else None
    return {"pinned_kpis": pinned}


@router.patch("/layout")
async def save_dashboard_layout(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    pinned_kpis = data.get("pinned_kpis", [])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO dashboard_preferences (user_id, pinned_kpis, updated_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET pinned_kpis = EXCLUDED.pinned_kpis, updated_at = EXCLUDED.updated_at
        """,
        (current_user["id"], json.dumps(pinned_kpis), datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return {"success": True, "pinned_kpis": pinned_kpis}
