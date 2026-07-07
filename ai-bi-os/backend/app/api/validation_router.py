from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.validation import (
    ValidateObjectRequest, ValidationResponse,
    ConfidenceScoreResponse, ReliabilityScoreResponse
)
from app.services.validation.validation_service import validation_service
from app.models.validation import ValidationRun

router = APIRouter(prefix="/api/v1/validation", tags=["validation"])

@router.post("/run", response_model=ValidationResponse)
async def run_validation(req: ValidateObjectRequest, db: Session = Depends(get_db)):
    """Trigger validation for an analytical object."""
    try:
        rules_dict = [r.dict() for r in req.rules]
        result = validation_service.validate_object(
            db=db,
            target_object_id=req.target_object_id,
            target_object_type=req.target_object_type,
            metadata=req.metadata,
            rules=rules_dict
        )
        return ValidationResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}/confidence", response_model=ConfidenceScoreResponse)
async def get_confidence(id: str, db: Session = Depends(get_db)):
    run = db.query(ValidationRun).filter(ValidationRun.id == id).first()
    if not run or not run.confidence:
        raise HTTPException(status_code=404, detail="Confidence scores not found")
        
    return ConfidenceScoreResponse(
        overall_confidence=run.confidence.overall_confidence,
        statistical_confidence=run.confidence.statistical_confidence,
        data_confidence=run.confidence.data_confidence,
        model_confidence=run.confidence.model_confidence,
        business_confidence=run.confidence.business_confidence,
        prediction_confidence=run.confidence.prediction_confidence,
        confidence_level=run.confidence.confidence_level,
        confidence_grade=run.confidence.confidence_grade
    )

@router.get("/{id}/reliability", response_model=ReliabilityScoreResponse)
async def get_reliability(id: str, db: Session = Depends(get_db)):
    run = db.query(ValidationRun).filter(ValidationRun.id == id).first()
    if not run or not run.reliability:
        raise HTTPException(status_code=404, detail="Reliability scores not found")
        
    return ReliabilityScoreResponse(
        reliability_score=run.reliability.reliability_score,
        trust_score=run.reliability.trust_score,
        business_readiness_score=run.reliability.business_readiness_score,
        production_readiness_score=run.reliability.production_readiness_score,
        explainability_score=run.reliability.explainability_score
    )
