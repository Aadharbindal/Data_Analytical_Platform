from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import uuid
import sqlite3
import json
import os
from app.services.data_processing import save_dataset, DB_PATH

router = APIRouter()

class UploadResponse(BaseModel):
    job_id: str
    status: str

@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...)):
    content = await file.read()
    dataset_info = save_dataset(content, file.filename)
    return {"job_id": dataset_info["id"], "status": "processing"}

from fastapi.responses import StreamingResponse
import asyncio

@router.get("/upload/status/{job_id}")
async def get_upload_status(job_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM datasets WHERE id=?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"status": "completed", "progress": 100}
    return {"status": "processing", "progress": 50}

@router.get("/upload/status/{job_id}/stream")
async def get_upload_status_stream(job_id: str):
    async def event_generator():
        yield f"data: {json.dumps({'status': 'processing', 'progress': 50, 'current_step': 'Parsing data'})}\n\n"
        await asyncio.sleep(0.5)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM datasets WHERE id=?", (job_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            yield f"data: {json.dumps({'status': 'completed', 'progress': 100})}\n\n"
        else:
            yield f"data: {json.dumps({'status': 'failed', 'error_message': 'Dataset not found'})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/")
async def list_datasets(workspace_id: Optional[str] = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, status, created_at, latest_version, filepath, columns FROM datasets')
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0], "name": r[1], "status": r[2], 
            "created_at": r[3], 
            "latest_version": json.loads(r[4]) if r[4] else {}, 
            "filepath": r[5], 
            "columns": json.loads(r[6]) if r[6] else []
        }
        for r in rows
    ]

@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get filepath to delete file
    cursor.execute("SELECT filepath FROM datasets WHERE id=?", (dataset_id,))
    row = cursor.fetchone()
    if row:
        filepath = row[0]
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
                
    cursor.execute("DELETE FROM datasets WHERE id=?", (dataset_id,))
    cursor.execute("DELETE FROM catalog WHERE id=?", (dataset_id,))
    
    # If active dataset was this one, clear it
    cursor.execute("SELECT dataset_id FROM active_dataset WHERE id=1")
    active_row = cursor.fetchone()
    if active_row and active_row[0] == dataset_id:
        cursor.execute("DELETE FROM active_dataset WHERE id=1")
        
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": "Dataset deleted"}
