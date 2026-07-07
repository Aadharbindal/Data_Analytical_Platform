from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os

from app.core.database import get_db
from app.models.dataset import DatasetVersion
from app.models.cleaning import CleaningRecommendation, CleaningHistory
from app.services.cleaning import RecommendationEngine, PreviewEngine, CleaningOrchestrator
from app.services.storage.local_provider import LocalStorageProvider
from app.schemas.cleaning import (
    CleaningRecommendationResponse, TransformationStepRequest, 
    PipelineApplyRequest, PreviewResponse, CleaningHistoryResponse
)

router = APIRouter(prefix="/api/v1/datasets/{dataset_id}/cleaning", tags=["cleaning"])

@router.get("/recommendations", response_model=List[CleaningRecommendationResponse])
def get_cleaning_recommendations(dataset_id: str, db: Session = Depends(get_db)):
    version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.is_active == True).first()
    if not version:
        raise HTTPException(status_code=404, detail="Active dataset version not found.")
        
    engine = RecommendationEngine(db)
    # Generate them on the fly from latest quality logs
    recs = engine.generate_recommendations(version.id)
    return recs

@router.post("/preview", response_model=PreviewResponse)
def preview_pipeline(dataset_id: str, payload: PipelineApplyRequest, db: Session = Depends(get_db)):
    version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.is_active == True).first()
    if not version:
        raise HTTPException(status_code=404, detail="Active dataset version not found.")
        
    provider = LocalStorageProvider()
    loc = version.storage_locations[0]
    full_path = os.path.join(provider.base_dir, loc.storage_path)
    
    steps_dict = [s.model_dump() for s in payload.steps]
    
    return PreviewEngine.generate_preview(full_path, version.file_type, steps_dict)

@router.post("/apply")
def apply_pipeline(dataset_id: str, payload: PipelineApplyRequest, db: Session = Depends(get_db)):
    """Triggers background pipeline execution"""
    from app.worker import apply_cleaning_pipeline_task
    steps_dict = [s.model_dump() for s in payload.steps]
    
    apply_cleaning_pipeline_task.delay(dataset_id, steps_dict)
    
    return {"status": "success", "message": "Transformation pipeline queued for execution."}

@router.post("/rollback")
def rollback_pipeline(dataset_id: str, db: Session = Depends(get_db)):
    orch = CleaningOrchestrator(db)
    try:
        new_version_id = orch.rollback(dataset_id)
        # We also need to re-trigger the schema parsing for the rolled back version 
        # so downstream profiles sync back to the old data.
        from app.worker import process_schema_task
        from app.models.dataset import DatasetVersion
        version = db.query(DatasetVersion).filter(DatasetVersion.id == new_version_id).first()
        storage = version.storage_locations[0]
        process_schema_task.delay(version.id, storage.storage_path, version.file_type)
        
        return {"status": "success", "message": "Rolled back successfully. Synchronizing metadata."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history", response_model=List[CleaningHistoryResponse])
def get_cleaning_history(dataset_id: str, db: Session = Depends(get_db)):
    history = db.query(CleaningHistory).filter(CleaningHistory.dataset_id == dataset_id).order_by(CleaningHistory.executed_at.desc()).all()
    return history
