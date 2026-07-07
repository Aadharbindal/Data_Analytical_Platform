from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.correlation import (
    RunCorrelationRequest, CorrelationRunResponse,
    FeatureRelationshipResponse, PairwiseCorrelationResponse
)
from app.services.correlation.correlation_service import correlation_service
from app.models.correlation import CorrelationRun

router = APIRouter(prefix="/api/v1/correlation", tags=["correlation"])

@router.post("/run", response_model=CorrelationRunResponse)
async def run_correlation(req: RunCorrelationRequest, db: Session = Depends(get_db)):
    """Trigger an Correlation run for a dataset."""
    try:
        result = correlation_service.run_correlation(
            db=db,
            dataset_id=req.dataset_id,
            dataset_version_id=req.dataset_version_id,
            columns_meta=req.columns_meta
        )
        return CorrelationRunResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_version_id}/relationships", response_model=List[FeatureRelationshipResponse])
async def get_feature_relationships(dataset_version_id: str, db: Session = Depends(get_db)):
    """Get the highest value business relationships discovered."""
    run = db.query(CorrelationRun).filter(
        CorrelationRun.dataset_version_id == dataset_version_id,
        CorrelationRun.status == "COMPLETED"
    ).order_by(CorrelationRun.generated_at.desc()).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Correlation Run not found")
        
    return [
        FeatureRelationshipResponse(
            source_metric=r.source_metric,
            target_metric=r.target_metric,
            relationship_type=r.relationship_type,
            business_relevance=r.business_relevance,
            supporting_statistics=r.supporting_statistics
        ) for r in run.feature_relationships
    ]

@router.get("/{dataset_version_id}/significant", response_model=List[PairwiseCorrelationResponse])
async def get_significant_pairs(dataset_version_id: str, db: Session = Depends(get_db)):
    """Get all statistically significant pairwise correlations."""
    run = db.query(CorrelationRun).filter(
        CorrelationRun.dataset_version_id == dataset_version_id,
        CorrelationRun.status == "COMPLETED"
    ).order_by(CorrelationRun.generated_at.desc()).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Correlation Run not found")
        
    sig_pairs = [p for p in run.numerical_results if p.is_significant]
    sig_pairs.extend([p for p in run.association_results if p.is_significant])
    
    return [
        PairwiseCorrelationResponse(
            column_x=p.column_x,
            column_y=p.column_y,
            method_used=p.method_used,
            coefficient=p.coefficient,
            p_value=p.p_value,
            is_significant=p.is_significant,
            strength_classification=p.strength_classification
        ) for p in sig_pairs
    ]
