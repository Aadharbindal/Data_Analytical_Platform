from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uuid
import sqlite3
import json
import os
from app.services.data_processing import save_dataset, DB_PATH, get_dataset_path, get_active_dataset, get_dataframe
from app.core.security import get_current_user
from app.services.stats_service import compute_kpis

router = APIRouter()

class UploadResponse(BaseModel):
    job_id: str
    status: str

@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    from app.core.config import MAX_UPLOAD_MB
    content = await file.read()
    
    # File size limit check
    max_size = MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"File size exceeds maximum limit of {MAX_UPLOAD_MB}MB.")
        
    try:
        dataset_info = save_dataset(content, file.filename, current_user["id"])
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")
        
    return {"job_id": dataset_info["id"], "status": "processing"}

from fastapi.responses import StreamingResponse
import asyncio

@router.get("/upload/status/{job_id}")
async def get_upload_status(job_id: str, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM datasets WHERE id=? AND user_id=?", (job_id, current_user["id"]))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"status": "completed", "progress": 100}
    return {"status": "processing", "progress": 50}

@router.get("/upload/status/{job_id}/stream")
async def get_upload_status_stream(job_id: str, current_user: dict = Depends(get_current_user)):
    async def event_generator():
        yield f"data: {json.dumps({'status': 'processing', 'progress': 50, 'current_step': 'Parsing data'})}\n\n"
        await asyncio.sleep(0.5)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM datasets WHERE id=? AND user_id=?", (job_id, current_user["id"]))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            yield f"data: {json.dumps({'status': 'completed', 'progress': 100})}\n\n"
        else:
            yield f"data: {json.dumps({'status': 'failed', 'error_message': 'Dataset not found'})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/active")
async def get_active_dataset_route(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
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
async def list_datasets(workspace_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, status, created_at, latest_version, filepath, columns, skipped_rows, sheet_name, version, quality_score FROM datasets WHERE user_id=? ORDER BY created_at DESC', (current_user["id"],))
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

@router.get("/compare")
async def compare_datasets(id_a: str, id_b: str, current_user: dict = Depends(get_current_user)):
    df_a = get_dataframe(id_a, current_user["id"])
    df_b = get_dataframe(id_b, current_user["id"])
    
    if df_a is None or df_b is None:
        raise HTTPException(status_code=400, detail="One or both datasets could not be loaded")
        
    # Schema diff
    cols_a = set(df_a.columns)
    cols_b = set(df_b.columns)
    only_in_a = list(cols_a - cols_b)
    only_in_b = list(cols_b - cols_a)
    common_cols = list(cols_a & cols_b)
    
    # KPI Diffs
    kpis_a = compute_kpis(df_a).get("kpis", [])
    kpis_b = compute_kpis(df_b).get("kpis", [])
    
    kpi_diffs = []
    for ka in kpis_a:
        for kb in kpis_b:
            if ka["name"] == kb["name"]:
                try:
                    val_a = float(str(ka["value"]).replace("$","").replace(",",""))
                    val_b = float(str(kb["value"]).replace("$","").replace(",",""))
                except ValueError:
                    val_a, val_b = 0, 0
                delta = val_b - val_a
                delta_pct = (delta / val_a) * 100 if val_a != 0 else 0
                
                kpi_diffs.append({
                    "name": ka["name"],
                    "value_a": val_a,
                    "value_b": val_b,
                    "delta": delta,
                    "delta_pct": delta_pct
                })
                break
                
    # Numeric column diffs (means)
    num_diffs = []
    import numpy as np
    import pandas as pd
    for col in common_cols:
        if pd.api.types.is_numeric_dtype(df_a[col]) and pd.api.types.is_numeric_dtype(df_b[col]):
            mean_a = float(df_a[col].mean()) if not pd.isna(df_a[col].mean()) else 0
            mean_b = float(df_b[col].mean()) if not pd.isna(df_b[col].mean()) else 0
            delta = mean_b - mean_a
            num_diffs.append({
                "column": col,
                "mean_a": mean_a,
                "mean_b": mean_b,
                "delta": delta
            })
            
    return {
        "schema_diff": {
            "only_in_a": only_in_a,
            "only_in_b": only_in_b,
            "common": common_cols
        },
        "kpi_diffs": kpi_diffs,
        "num_diffs": num_diffs,
        "rows_a": len(df_a),
        "rows_b": len(df_b)
    }

@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, status, created_at, latest_version, filepath, columns, skipped_rows, sheet_name, version, quality_score FROM datasets WHERE id=? AND user_id=?', (dataset_id, current_user["id"]))
    r = cursor.fetchone()
    conn.close()
    if not r:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return {
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

@router.post("/{dataset_id}/activate")
async def activate_dataset(dataset_id: str, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM datasets WHERE id=? AND user_id=?", (dataset_id, current_user["id"]))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    cursor.execute("INSERT OR REPLACE INTO active_dataset (user_id, dataset_id) VALUES (?, ?)", (current_user["id"], dataset_id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Dataset {dataset_id} activated"}

@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get filepath to delete file
    cursor.execute("SELECT filepath FROM datasets WHERE id=? AND user_id=?", (dataset_id, current_user["id"]))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    filename_db = row[0]
    if filename_db:
        disk_path = get_dataset_path(filename_db)
        if os.path.exists(disk_path):
            try:
                os.remove(disk_path)
            except Exception:
                pass
                    
    cursor.execute("DELETE FROM datasets WHERE id=? AND user_id=?", (dataset_id, current_user["id"]))
    cursor.execute("DELETE FROM catalog WHERE id=? AND user_id=?", (dataset_id, current_user["id"]))
    
    # If active dataset was this one, fallback to most recent remaining
    cursor.execute("SELECT dataset_id FROM active_dataset WHERE user_id=?", (current_user["id"],))
    active_row = cursor.fetchone()
    if active_row and active_row[0] == dataset_id:
        cursor.execute("SELECT id FROM datasets WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (current_user["id"],))
        next_row = cursor.fetchone()
        if next_row:
            cursor.execute("INSERT OR REPLACE INTO active_dataset (user_id, dataset_id) VALUES (?, ?)", (current_user["id"], next_row[0]))
        else:
            cursor.execute("DELETE FROM active_dataset WHERE user_id=?", (current_user["id"],))
            
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": "Dataset deleted"}
