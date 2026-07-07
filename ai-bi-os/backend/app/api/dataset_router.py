from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.core.database import get_db
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_registry_service import DatasetRegistryService
from app.services.dataset_version_service import DatasetVersionService
from app.schemas.dataset import DatasetResponse, DatasetListResponse, DatasetUpdateRequest, UploadJobResponse, DatasetVersionResponse
from app.services.storage_service import StorageService
from app.worker import process_upload_task

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])

# Mock dependencies for Module 2
def get_current_user():
    return "user-123"

def get_current_workspace():
    return "workspace-123"

@router.get("", response_model=List[DatasetResponse])
def get_datasets(
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    project_id: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    status: Optional[str] = Query("active"),
    limit: int = Query(50),
    offset: int = Query(0)
):
    """Browse the dataset catalog with filters."""
    registry = DatasetRegistryService(db)
    return registry.list_datasets(
        workspace_id=workspace_id,
        project_id=project_id, 
        owner_id=owner_id, 
        status=status, 
        limit=limit, 
        offset=offset
    )

@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    registry = DatasetRegistryService(db)
    dataset = registry.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset

@router.patch("/{dataset_id}", response_model=DatasetResponse)
def update_dataset(
    dataset_id: str,
    payload: DatasetUpdateRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    registry = DatasetRegistryService(db)
    dataset = registry.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    updates = payload.dict(exclude_unset=True)
    for key, value in updates.items():
        setattr(dataset, key, value)
    
    registry.log_history(dataset_id, user_id, "rename/update", details=updates)
    db.commit()
    db.refresh(dataset)
    return dataset

@router.get("/{dataset_id}/versions", response_model=List[DatasetVersionResponse])
def get_dataset_versions(dataset_id: str, db: Session = Depends(get_db)):
    version_service = DatasetVersionService(db)
    versions = version_service.get_versions(dataset_id)
    return versions

@router.get("/{dataset_id}/latest", response_model=DatasetVersionResponse)
def get_dataset_latest_version(dataset_id: str, db: Session = Depends(get_db)):
    version_service = DatasetVersionService(db)
    latest = version_service.get_latest_version(dataset_id)
    if not latest:
        raise HTTPException(status_code=404, detail="No active versions found for this dataset")
    return latest

@router.post("/{dataset_id}/restore/{version_number}")
def restore_dataset_version(
    dataset_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """Rolls back the dataset to a specific version."""
    version_service = DatasetVersionService(db)
    registry = DatasetRegistryService(db)
    
    success = version_service.rollback_version(dataset_id, version_number)
    if not success:
        raise HTTPException(status_code=404, detail=f"Version {version_number} not found for dataset {dataset_id}")
    
    registry.log_history(dataset_id, user_id, "restore", details={"restored_to_version": version_number})
    return {"status": "success", "message": f"Dataset restored to version {version_number}"}

@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: str, 
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """Soft deletes a dataset."""
    registry = DatasetRegistryService(db)
    success = registry.soft_delete_dataset(dataset_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found or already deleted")
    return {"status": "success", "message": "Dataset deleted"}

# --- UPLOAD ENDPOINTS FROM MODULE 1 ---

@router.post("/upload/chunk")
async def upload_chunk(
    job_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    filename: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    storage = StorageService()
    content = await file.read()
    
    try:
        storage.save_chunk(job_id, chunk_index, content)
        
        # If this is the last chunk, we trigger merge and process
        if chunk_index == total_chunks - 1:
            # Note: For chunked uploads, we must first figure out the destination path.
            # However, the final destination path requires the Dataset ID (which might be created by the worker).
            # So for now, we just merge it in a temp location, and let the worker handle moving it.
            # We'll pass a temporary target path.
            temp_path = f"temp/{job_id}_{filename}"
            final_path = storage.merge_chunks_to_provider(job_id, total_chunks, temp_path)
            
            process_upload_task.delay(job_id, final_path, filename)
            
            return {"status": "success", "message": "All chunks received, processing started."}
            
        return {"status": "success", "message": f"Chunk {chunk_index} saved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_dataset_direct(
    dataset_name: Optional[str] = Form(None),
    dataset_id: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    workspace_id: str = Depends(get_current_workspace)
):
    repo = DatasetRepository(db)
    storage = StorageService()
    
    job = repo.create_upload_job(user_id, workspace_id, dataset_name, dataset_id)
    if project_id:
        job.project_id = project_id
        db.commit()
        
    content = await file.read()
    temp_path = f"temp/{job.id}_{file.filename}"
    final_path = storage.save_direct_upload(temp_path, content)
    
    process_upload_task.delay(job.id, final_path, file.filename)
    
    return {"status": "success", "job_id": job.id, "message": "File received, processing started."}

@router.get("/upload/status/{job_id}", response_model=UploadJobResponse)
def get_upload_status(job_id: str, db: Session = Depends(get_db)):
    repo = DatasetRepository(db)
    job = repo.get_upload_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

from fastapi.responses import StreamingResponse
import asyncio
import json
from app.core.database import SessionLocal
from app.models.dataset import UploadJob

@router.get("/upload/status/{job_id}/stream")
async def stream_upload_status(job_id: str):
    async def event_generator():
        while True:
            db = SessionLocal()
            try:
                job = db.query(UploadJob).filter(UploadJob.id == job_id).first()
                if not job:
                    yield f"data: {json.dumps({'status': 'failed', 'error_message': 'Job not found'})}\n\n"
                    break
                
                payload = {
                    "id": job.id,
                    "status": job.status,
                    "current_step": job.current_step,
                    "progress": job.progress,
                    "error_message": job.error_message
                }
                yield f"data: {json.dumps(payload)}\n\n"
                
                if job.status in ["completed", "failed"]:
                    break
            finally:
                db.close()
            await asyncio.sleep(1)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
