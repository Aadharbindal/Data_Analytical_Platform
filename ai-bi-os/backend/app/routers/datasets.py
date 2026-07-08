from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import uuid
from app.services.data_processing import save_dataset, db

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
import json

@router.get("/upload/status/{job_id}")
async def get_upload_status(job_id: str):
    if job_id in db["datasets"]:
        return {"status": "completed", "progress": 100}
    return {"status": "processing", "progress": 50}

@router.get("/upload/status/{job_id}/stream")
async def get_upload_status_stream(job_id: str):
    async def event_generator():
        # Quick stream for instant upload simulation
        yield f"data: {json.dumps({'status': 'processing', 'progress': 50, 'current_step': 'Parsing data'})}\n\n"
        await asyncio.sleep(0.5)
        if job_id in db["datasets"]:
            yield f"data: {json.dumps({'status': 'completed', 'progress': 100})}\n\n"
        else:
            yield f"data: {json.dumps({'status': 'failed', 'error_message': 'Dataset not found'})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/")
async def list_datasets(workspace_id: Optional[str] = None):
    return list(db["datasets"].values())

@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str):
    if dataset_id in db["datasets"]:
        # Optional: delete file from disk as well
        import os
        filepath = db["datasets"][dataset_id].get("filepath")
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
        
        del db["datasets"][dataset_id]
        
        # Also clean up catalog if needed
        db["catalog"] = [c for c in db["catalog"] if c["id"] != dataset_id]
        
        if db["active_dataset_id"] == dataset_id:
            db["active_dataset_id"] = None
            
        return {"status": "success", "message": "Dataset deleted"}
    return {"status": "error", "message": "Dataset not found"}
