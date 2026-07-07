from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.forecast import (
    RunForecastRequest, ForecastRunResponse, ForecastSummaryResponse,
    ForecastModelSchema, PredictionPointSchema, ScenarioSchema
)
from app.services.forecast.forecast_service import forecast_service
from app.models.forecast import ForecastRun, ForecastModel

router = APIRouter(prefix="/api/v1/forecast", tags=["forecast"])

@router.post("/run", response_model=ForecastRunResponse)
async def run_forecast_analysis(req: RunForecastRequest, db: Session = Depends(get_db)):
    """Trigger forecast generation for metrics in a dataset."""
    try:
        metrics_dict = [m.dict() for m in req.metrics]
        result = forecast_service.run_forecast_analysis(
            db=db,
            dataset_id=req.dataset_id,
            dataset_version_id=req.dataset_version_id,
            metrics=metrics_dict
        )
        return ForecastRunResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/summary", response_model=List[ForecastSummaryResponse])
async def get_forecast_summary(dataset_id: str, db: Session = Depends(get_db)):
    run = db.query(ForecastRun).filter(
        ForecastRun.dataset_id == dataset_id,
        ForecastRun.status == "COMPLETED"
    ).order_by(ForecastRun.created_at.desc()).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Forecast run not found")
        
    res = []
    # Group by column to find the selected model
    cols = set(m.column_name for m in run.models)
    
    for c in cols:
        sel = next((m for m in run.models if m.column_name == c and m.is_selected), None)
        if sel:
            res.append(ForecastSummaryResponse(
                column_name=sel.column_name,
                selected_model=sel.model_name,
                rmse=sel.rmse,
                aic=sel.aic
            ))
            
    return res
