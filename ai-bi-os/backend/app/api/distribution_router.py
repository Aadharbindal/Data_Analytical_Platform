from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.distribution import (
    RunDistributionRequest, DistributionRunResponse, DistributionProfileResponse,
    DistributionFitSchema, DensityProfileSchema
)
from app.services.distribution.distribution_service import distribution_service
from app.models.distribution import DistributionRun, DistributionProfile, DistributionFit

router = APIRouter(prefix="/api/v1/distribution", tags=["distribution"])

@router.post("/run", response_model=DistributionRunResponse)
async def run_distribution(req: RunDistributionRequest, db: Session = Depends(get_db)):
    """Trigger distribution analysis for columns in a dataset."""
    try:
        columns_dict = [c.dict() for c in req.columns]
        result = distribution_service.run_distribution_analysis(
            db=db,
            dataset_id=req.dataset_id,
            dataset_version_id=req.dataset_version_id,
            columns=columns_dict
        )
        return DistributionRunResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/profiles", response_model=List[DistributionProfileResponse])
async def get_profiles(dataset_id: str, db: Session = Depends(get_db)):
    run = db.query(DistributionRun).filter(
        DistributionRun.dataset_id == dataset_id,
        DistributionRun.status == "COMPLETED"
    ).order_by(DistributionRun.created_at.desc()).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Distribution run not found")
        
    responses = []
    for p in run.profiles:
        best_fit = None
        for f in p.fits:
            if f.is_best_fit: best_fit = f.distribution_type
            
        responses.append(DistributionProfileResponse(
            column_name=p.column_name,
            column_type=p.column_type,
            mean=p.mean,
            median=p.median,
            variance=p.variance,
            skewness=p.skewness,
            kurtosis=p.kurtosis,
            entropy=p.entropy,
            is_heavy_tail=p.tail.is_heavy_tail if p.tail else None,
            modality=p.tail.modality if p.tail else None,
            best_fit=best_fit
        ))
        
    return responses
