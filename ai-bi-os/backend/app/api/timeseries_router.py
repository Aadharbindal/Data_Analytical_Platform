from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.timeseries import (
    RunTimeSeriesRequest, TimeSeriesRunResponse, TimeSeriesSummaryResponse
)
from app.services.timeseries.timeseries_service import timeseries_service
from app.models.timeseries import TimeSeriesRun

router = APIRouter(prefix="/api/v1/timeseries", tags=["timeseries"])

@router.post("/run", response_model=TimeSeriesRunResponse)
async def run_timeseries_analysis(req: RunTimeSeriesRequest, db: Session = Depends(get_db)):
    """Trigger time series analysis for columns in a dataset."""
    try:
        columns_dict = [c.dict() for c in req.columns]
        result = timeseries_service.run_temporal_analysis(
            db=db,
            dataset_id=req.dataset_id,
            dataset_version_id=req.dataset_version_id,
            columns=columns_dict
        )
        return TimeSeriesRunResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/summary", response_model=List[TimeSeriesSummaryResponse])
async def get_timeseries_summary(dataset_id: str, db: Session = Depends(get_db)):
    run = db.query(TimeSeriesRun).filter(
        TimeSeriesRun.dataset_id == dataset_id,
        TimeSeriesRun.status == "COMPLETED"
    ).order_by(TimeSeriesRun.created_at.desc()).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="TimeSeries run not found")
        
    res = []
    for p in run.profiles:
        res.append(TimeSeriesSummaryResponse(
            column_name=p.column_name,
            metric_name=p.metric_name,
            temporal_quality_score=p.temporal_quality_score or 0.0,
            temporal_completeness=p.temporal_completeness or 0.0,
            inferred_frequency=p.frequency.inferred_frequency if p.frequency else None,
            continuity_score=p.gaps.continuity_score if p.gaps else None
        ))
        
    return res
