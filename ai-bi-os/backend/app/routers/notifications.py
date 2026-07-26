from fastapi import APIRouter, Depends
from app.core.database import get_db_connection
from app.core.security import get_current_user

router = APIRouter()


@router.get("")
async def list_notifications(limit: int = 30, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT %s',
        (current_user["id"], limit),
    )
    items = [dict(r) for r in cursor.fetchall()]
    cursor.execute(
        'SELECT COUNT(*) AS c FROM notifications WHERE user_id = %s AND is_read = 0',
        (current_user["id"],),
    )
    row = cursor.fetchone()
    conn.close()
    return {"items": items, "unread_count": (row["c"] if row else 0)}


@router.patch("/{notif_id}")
async def mark_notification_read(notif_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s',
        (notif_id, current_user["id"]),
    )
    conn.commit()
    conn.close()
    return {"success": True}


@router.post("/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0',
        (current_user["id"],),
    )
    conn.commit()
    conn.close()
    return {"success": True}


@router.delete("/{notif_id}")
async def delete_notification(notif_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM notifications WHERE id = %s AND user_id = %s',
        (notif_id, current_user["id"]),
    )
    conn.commit()
    conn.close()
    return {"success": True}
