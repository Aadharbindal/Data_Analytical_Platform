from fastapi import APIRouter
from typing import Optional
import sqlite3
import json
from app.services.data_processing import DB_PATH

router = APIRouter()

@router.get("/")
async def list_catalog(workspace_id: Optional[str] = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, domain, description, owner, tags FROM catalog')
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0], "name": r[1], "domain": r[2], 
            "description": r[3], "owner": r[4], 
            "tags": json.loads(r[5]) if r[5] else []
        }
        for r in rows
    ]

@router.get("/search")
async def search_catalog(q: str):
    query = f"%{q.lower()}%"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, domain, description, owner, tags FROM catalog WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ?', (query, query))
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0], "name": r[1], "domain": r[2], 
            "description": r[3], "owner": r[4], 
            "tags": json.loads(r[5]) if r[5] else []
        }
        for r in rows
    ]
