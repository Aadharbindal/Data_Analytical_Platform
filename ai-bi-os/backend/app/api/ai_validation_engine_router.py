from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.ai_validation_engine import (
    ValidationRequest,
    RevalidationRequest,
    ValidationResponse,
    ValidationListResponse,
    ValidationStatisticsResponse
)
from app.services.ai_validation_engine.validation_pipeline import ValidationPipeline
from app.repositories.ai_validation_engine_repository import AIValidationEngineRepository

router = APIRouter(prefix="/ai-validator", tags=["ai-validation-engine"])

@router.post("/validate", response_model=ValidationResponse)
def validate_output(request: ValidationRequest, db: Session = Depends(get_db)):
    pipeline = ValidationPipeline(db)
    try:
        val_obj = pipeline.validate(
            workspace_id=request.workspace_id,
            object_id=request.object_id,
            object_type=request.object_type,
            payload=request.payload
        )
        return val_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/revalidate", response_model=ValidationResponse)
def revalidate_output(request: RevalidationRequest, db: Session = Depends(get_db)):
    repo = AIValidationEngineRepository(db)
    val_obj = repo.get_validation(request.validation_id)
    if not val_obj:
        raise HTTPException(status_code=404, detail="Validation not found")
    
    # In a real scenario, we would re-fetch the payload. For now, returning existing.
    return val_obj

@router.get("/history", response_model=ValidationListResponse)
def get_validation_history(db: Session = Depends(get_db)):
    repo = AIValidationEngineRepository(db)
    vals = repo.list_validations()
    return ValidationListResponse(validations=vals, total=len(vals))

@router.get("/statistics", response_model=ValidationStatisticsResponse)
def get_validation_statistics(db: Session = Depends(get_db)):
    repo = AIValidationEngineRepository(db)
    return repo.get_statistics()

@router.get("/{validation_id}", response_model=ValidationResponse)
def get_validation(validation_id: str, db: Session = Depends(get_db)):
    repo = AIValidationEngineRepository(db)
    val_obj = repo.get_validation(validation_id)
    if not val_obj:
        raise HTTPException(status_code=404, detail="Validation not found")
    return val_obj
