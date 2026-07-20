from fastapi import APIRouter, Depends
from typing import Optional
from app.core.database import get_db_connection
import json
from app.services.data_processing import DB_PATH
from app.core.security import get_current_user

router = APIRouter()

@router.get("")
async def list_catalog(workspace_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, domain, description, owner, tags FROM catalog WHERE user_id = ?', (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0], "name": r[1], "domain": r[2], 
            "description": r[3], "owner": r[4], 
            "tags": (r[5] if isinstance(r[5], (dict, list)) else json.loads(r[5])) if r[5] else []
        }
        for r in rows
    ]

@router.get("/search")
async def search_catalog(q: str, current_user: dict = Depends(get_current_user)):
    query = f"%{q.lower()}%"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, domain, description, owner, tags FROM catalog WHERE user_id = ? AND (LOWER(name) LIKE ? OR LOWER(description) LIKE ?)', (current_user["id"], query, query))
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0], "name": r[1], "domain": r[2], 
            "description": r[3], "owner": r[4], 
            "tags": (r[5] if isinstance(r[5], (dict, list)) else json.loads(r[5])) if r[5] else []
        }
        for r in rows
    ]
