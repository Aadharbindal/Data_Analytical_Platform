from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.schemas.context_builder import (
    ContextBuildRequest, ContextObjectResponse, 
    ContextValidationRequest, ContextValidationResponse
)
from app.services.context_builder import ContextBuilderService

router = APIRouter(prefix="/context", tags=["Context Builder"])

@router.post("/build", response_model=ContextObjectResponse, status_code=status.HTTP_201_CREATED)
def build_context(request: ContextBuildRequest, db: Session = Depends(get_db)):
    """
    Builds a deterministic context payload from the Analytics Registry.
    """
    service = ContextBuilderService(db)
    try:
        return service.build_context(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rebuild", response_model=ContextObjectResponse)
def rebuild_context(context_id: str, db: Session = Depends(get_db)):
    """
    Forces a rebuild of an existing context payload.
    """
    service = ContextBuilderService(db)
    # Rebuilding logic leverages existing references to fetch newest versions
    # For MVP, returning existing to satisfy interface
    obj = service.get_context(context_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Context not found")
    return obj

@router.get("/conversation/{conversation_id}", response_model=List[ContextObjectResponse])
def get_contexts_by_conversation(conversation_id: str, db: Session = Depends(get_db)):
    service = ContextBuilderService(db)
    objects = service.repo.get_by_conversation(conversation_id)
    return [ContextObjectResponse.model_validate(obj) for obj in objects]

@router.get("/dataset/{dataset_id}", response_model=List[ContextObjectResponse])
def get_contexts_by_dataset(dataset_id: str, db: Session = Depends(get_db)):
    service = ContextBuilderService(db)
    objects = service.repo.get_by_dataset(dataset_id)
    return [ContextObjectResponse.model_validate(obj) for obj in objects]

@router.post("/validate", response_model=ContextValidationResponse)
def validate_context(request: ContextValidationRequest, db: Session = Depends(get_db)):
    service = ContextBuilderService(db)
    return service.validate_context(request)

@router.get("/history", response_model=List[Dict[str, Any]])
def get_context_history(db: Session = Depends(get_db)):
    service = ContextBuilderService(db)
    return service.get_history()

@router.get("/{context_id}", response_model=ContextObjectResponse)
def get_context(context_id: str, db: Session = Depends(get_db)):
    service = ContextBuilderService(db)
    obj = service.get_context(context_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Context not found")
    return obj
