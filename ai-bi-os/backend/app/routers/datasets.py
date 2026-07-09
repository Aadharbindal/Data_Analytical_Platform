from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
import sqlite3
import json
import os
from app.services.data_processing import save_dataset, DB_PATH, get_dataset_path, get_active_dataset

router = APIRouter()

class UploadResponse(BaseModel):
    job_id: str
    status: str

@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...)):
    from app.core.config import MAX_UPLOAD_MB
    content = await file.read()
    
    # File size limit check
    max_size = MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"File size exceeds maximum limit of {MAX_UPLOAD_MB}MB.")
        
    try:
        dataset_info = save_dataset(content, file.filename)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")
        
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

@router.get("/active")
async def get_active_dataset_route():
    dataset_info = get_active_dataset()
    if not dataset_info:
        return None
    return {
        "id": dataset_info["id"],
        "name": dataset_info["name"],
        "row_count": dataset_info["latest_version"].get("row_count") if dataset_info.get("latest_version") else None,
        "columns": dataset_info["columns"],
        "skipped_rows": dataset_info.get("skipped_rows", 0),
        "sheet_name": dataset_info.get("sheet_name"),
        "version": dataset_info.get("version", 1),
        "quality_score": dataset_info.get("quality_score", 0)
    }

@router.get("/")
async def list_datasets(workspace_id: Optional[str] = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, status, created_at, latest_version, filepath, columns, skipped_rows, sheet_name, version, quality_score FROM datasets ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0], "name": r[1], "status": r[2], 
            "created_at": r[3], 
            "latest_version": json.loads(r[4]) if r[4] else {}, 
            "filepath": r[5], 
            "columns": json.loads(r[6]) if r[6] else [],
            "skipped_rows": r[7],
            "sheet_name": r[8],
            "version": r[9],
            "quality_score": r[10]
        }
        for r in rows
    ]

@router.post("/{dataset_id}/activate")
async def activate_dataset(dataset_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM datasets WHERE id=?", (dataset_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    cursor.execute("INSERT OR REPLACE INTO active_dataset (id, dataset_id) VALUES (1, ?)", (dataset_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Dataset {dataset_id} activated"}

@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get filepath to delete file
    cursor.execute("SELECT filepath FROM datasets WHERE id=?", (dataset_id,))
    row = cursor.fetchone()
    if row:
        filename_db = row[0]
        if filename_db:
            disk_path = get_dataset_path(filename_db)
            if os.path.exists(disk_path):
                try:
                    os.remove(disk_path)
                except Exception:
                    pass
                    
    cursor.execute("DELETE FROM datasets WHERE id=?", (dataset_id,))
    cursor.execute("DELETE FROM catalog WHERE id=?", (dataset_id,))
    
    # If active dataset was this one, fallback to most recent remaining
    cursor.execute("SELECT dataset_id FROM active_dataset WHERE id=1")
    active_row = cursor.fetchone()
    if active_row and active_row[0] == dataset_id:
        cursor.execute("SELECT id FROM datasets ORDER BY created_at DESC LIMIT 1")
        next_row = cursor.fetchone()
        if next_row:
            cursor.execute("INSERT OR REPLACE INTO active_dataset (id, dataset_id) VALUES (1, ?)", (next_row[0],))
        else:
            cursor.execute("DELETE FROM active_dataset WHERE id=1")
            
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": "Dataset deleted"}

