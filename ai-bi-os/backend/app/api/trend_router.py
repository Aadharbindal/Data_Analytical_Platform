from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.trend import (
    RunTrendRequest, TrendRunResponse, TrendSummaryResponse,
    TrendSegmentSchema, ChangePointSchema
)
from app.services.trend.trend_service import trend_service
from app.models.trend import TrendRun

router = APIRouter(prefix="/api/v1/trends", tags=["trend"])

@router.post("/run", response_model=TrendRunResponse)
async def run_trend_analysis(req: RunTrendRequest, db: Session = Depends(get_db)):
    """Trigger trend analysis for columns in a dataset."""
    try:
        columns_dict = [c.dict() for c in req.columns]
        result = trend_service.run_trend_analysis(
            db=db,
            dataset_id=req.dataset_id,
            dataset_version_id=req.dataset_version_id,
            columns=columns_dict
        )
        return TrendRunResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/summary", response_model=List[TrendSummaryResponse])
async def get_trend_summary(dataset_id: str, db: Session = Depends(get_db)):
    run = db.query(TrendRun).filter(
        TrendRun.dataset_id == dataset_id,
        TrendRun.status == "COMPLETED"
    ).order_by(TrendRun.created_at.desc()).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Trend run not found")
        
    res = []
    for p in run.profiles:
        res.append(TrendSummaryResponse(
            column_name=p.column_name,
            overall_trend=p.overall_trend,
            signal_to_noise_ratio=p.signal_to_noise_ratio or 0.0,
            increasing_segments=sum(1 for s in p.segments if s.trend_direction == 'UP'),
            decreasing_segments=sum(1 for s in p.segments if s.trend_direction == 'DOWN'),
            change_points_count=len(p.change_points)
        ))
        
    return res
