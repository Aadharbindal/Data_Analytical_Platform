from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.statistics import (
    RunStatisticsRequest, StatisticsRunResponse,
    HypothesisTestResponse, ConfidenceIntervalResponse,
    DistributionProfileResponse, InferenceResultResponse
)
from app.services.statistics.statistical_service import statistical_service
from app.models.statistics import StatisticalRun

router = APIRouter(prefix="/api/v1/statistics", tags=["statistics"])

@router.post("/run", response_model=StatisticsRunResponse)
async def run_statistics(req: RunStatisticsRequest, db: Session = Depends(get_db)):
    """Trigger a statistical inference run for a dataset."""
    try:
        result = statistical_service.run_statistics(
            db=db,
            dataset_id=req.dataset_id,
            dataset_version_id=req.dataset_version_id,
            population_size=req.population_size,
            metrics=req.metrics
        )
        return StatisticsRunResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_version_id}/summary", response_model=List[InferenceResultResponse])
async def get_inference_summary(dataset_version_id: str, db: Session = Depends(get_db)):
    """Get the high-level business interpretations of statistical tests."""
    run = db.query(StatisticalRun).filter(
        StatisticalRun.dataset_version_id == dataset_version_id,
        StatisticalRun.status == "COMPLETED"
    ).order_by(StatisticalRun.generated_at.desc()).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Statistical Run not found")
        
    return [
        InferenceResultResponse(
            business_metric=r.business_metric,
            statistical_method=r.statistical_method,
            significance_level=r.significance_level,
            confidence_description=r.confidence_description,
            risk_level=r.risk_level,
            supporting_statistics=r.supporting_statistics
        ) for r in run.inference_results
    ]

@router.get("/{dataset_version_id}/hypothesis", response_model=List[HypothesisTestResponse])
async def get_hypothesis_tests(dataset_version_id: str, db: Session = Depends(get_db)):
    run = db.query(StatisticalRun).filter(
        StatisticalRun.dataset_version_id == dataset_version_id,
        StatisticalRun.status == "COMPLETED"
    ).order_by(StatisticalRun.generated_at.desc()).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Statistical Run not found")
        
    return [
        HypothesisTestResponse(
            test_name=h.test_name,
            target_metric=h.target_metric,
            test_statistic=h.test_statistic,
            p_value=h.p_value,
            degrees_of_freedom=h.degrees_of_freedom,
            reject_null_hypothesis=h.reject_null_hypothesis
        ) for h in run.hypothesis_tests
    ]
