from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.profiling.profile_registry import ProfileRegistryService
from app.schemas.profile import DatasetProfileResponse, DatasetProfileSummaryResponse, ColumnProfileResponse

router = APIRouter(prefix="/api/v1/datasets/{dataset_id}/profile", tags=["profile"])

@router.get("", response_model=DatasetProfileResponse)
def get_dataset_profile(dataset_id: str, db: Session = Depends(get_db)):
    registry = ProfileRegistryService(db)
    profile = registry.get_profile_for_dataset(dataset_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found or still processing")
    return profile

@router.get("/summary", response_model=DatasetProfileSummaryResponse)
def get_dataset_profile_summary(dataset_id: str, db: Session = Depends(get_db)):
    registry = ProfileRegistryService(db)
    profile = registry.get_profile_for_dataset(dataset_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.get("/columns", response_model=List[ColumnProfileResponse])
def get_profile_columns(dataset_id: str, db: Session = Depends(get_db)):
    registry = ProfileRegistryService(db)
    profile = registry.get_profile_for_dataset(dataset_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile.columns

@router.post("/rebuild")
def rebuild_dataset_profile(dataset_id: str, db: Session = Depends(get_db)):
    """Triggers a background rebuild of the profile for the latest version."""
    from app.models.dataset import DatasetVersion
    from app.worker import process_profile_task
    
    latest_version = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id,
        DatasetVersion.is_active == True
    ).first()
    
    if not latest_version:
        raise HTTPException(status_code=404, detail="No active version found")
        
    storage = latest_version.storage_locations[0]
    
    process_profile_task.delay(latest_version.id, storage.storage_path, latest_version.file_type)
    return {"status": "success", "message": "Profile rebuild queued."}
