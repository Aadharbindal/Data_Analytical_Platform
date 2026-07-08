from fastapi import APIRouter
from typing import Optional
from app.services.data_processing import db

router = APIRouter()

@router.get("/")
async def list_catalog(workspace_id: Optional[str] = None):
    return db["catalog"]

@router.get("/search")
async def search_catalog(q: str):
    query = q.lower()
    results = [entry for entry in db["catalog"] if query in entry["name"].lower() or query in entry["description"].lower()]
    return results
