from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.outlier import (
    RunOutlierRequest, OutlierRunResponse, OutlierResultSchema,
    ExtremeValueSchema, OutlierSummarySchema
)
from app.services.outlier.outlier_service import outlier_service
from app.models.outlier import OutlierRun

router = APIRouter(prefix="/api/v1/outliers", tags=["outlier"])

@router.post("/run", response_model=OutlierRunResponse)
async def run_outlier_detection(req: RunOutlierRequest, db: Session = Depends(get_db)):
    """Trigger outlier analysis for columns in a dataset."""
    try:
        columns_dict = [c.dict() for c in req.columns]
        result = outlier_service.run_outlier_analysis(
            db=db,
            dataset_id=req.dataset_id,
            dataset_version_id=req.dataset_version_id,
            columns=columns_dict
        )
        return OutlierRunResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/summary", response_model=List[OutlierSummarySchema])
async def get_outlier_summary(dataset_id: str, db: Session = Depends(get_db)):
    run = db.query(OutlierRun).filter(
        OutlierRun.dataset_id == dataset_id,
        OutlierRun.status == "COMPLETED"
    ).order_by(OutlierRun.created_at.desc()).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Outlier run not found")
        
    return [OutlierSummarySchema(
        column_name=s.column_name,
        total_outliers=s.total_outliers,
        outlier_percentage=s.outlier_percentage
    ) for s in run.summaries]
    
@router.get("/{dataset_id}/columns", response_model=List[OutlierResultSchema])
async def get_outlier_results(dataset_id: str, db: Session = Depends(get_db)):
    run = db.query(OutlierRun).filter(
        OutlierRun.dataset_id == dataset_id,
        OutlierRun.status == "COMPLETED"
    ).order_by(OutlierRun.created_at.desc()).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Outlier run not found")
        
    return [OutlierResultSchema(
        column_name=r.column_name,
        row_reference=r.row_reference,
        detection_method=r.detection_method,
        severity=r.severity,
        outlier_type=r.outlier_type,
        actual_value=r.actual_value,
        distance_from_mean=r.distance_from_mean,
        distance_from_median=r.distance_from_median,
        business_impact=r.business_impact,
        risk_score=r.risk_score
    ) for r in run.results]
