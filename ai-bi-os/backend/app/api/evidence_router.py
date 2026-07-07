from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.schemas.evidence import (
    EvidenceBuildRequest, EvidenceObjectResponse, 
    EvidenceValidationRequest
)
from app.services.evidence_engine import EvidenceService

router = APIRouter(prefix="/evidence", tags=["Evidence Engine"])

@router.post("/build", response_model=EvidenceObjectResponse, status_code=status.HTTP_201_CREATED)
def build_evidence(request: EvidenceBuildRequest, db: Session = Depends(get_db)):
    """
    Builds a structured Evidence Object from a deterministic Context Object.
    (Currently synchronous for MVP, easily offloaded to Celery later)
    """
    service = EvidenceService(db)
    try:
        return service.build_evidence(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rebuild", response_model=EvidenceObjectResponse)
def rebuild_evidence(evidence_id: str, db: Session = Depends(get_db)):
    """
    Forces a rebuild of an existing evidence payload.
    """
    service = EvidenceService(db)
    obj = service.get_evidence(evidence_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return obj

@router.get("/context/{context_id}", response_model=List[EvidenceObjectResponse])
def get_evidence_by_context(context_id: str, db: Session = Depends(get_db)):
    service = EvidenceService(db)
    objects = service.repo.get_by_context(context_id)
    return [EvidenceObjectResponse.model_validate(obj) for obj in objects]

@router.get("/dataset/{dataset_id}", response_model=List[EvidenceObjectResponse])
def get_evidence_by_dataset(dataset_id: str, db: Session = Depends(get_db)):
    service = EvidenceService(db)
    objects = service.repo.get_by_dataset(dataset_id)
    return [EvidenceObjectResponse.model_validate(obj) for obj in objects]

@router.post("/validate")
def validate_evidence(request: EvidenceValidationRequest, db: Session = Depends(get_db)):
    service = EvidenceService(db)
    return service.validate_evidence(request)

@router.get("/history", response_model=List[Dict[str, Any]])
def get_evidence_history(db: Session = Depends(get_db)):
    service = EvidenceService(db)
    return service.get_history()

@router.get("/conflicts", response_model=List[Dict[str, Any]])
def get_evidence_conflicts(db: Session = Depends(get_db)):
    service = EvidenceService(db)
    return service.get_conflicts()

@router.get("/{evidence_id}", response_model=EvidenceObjectResponse)
def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    service = EvidenceService(db)
    obj = service.get_evidence(evidence_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return obj
