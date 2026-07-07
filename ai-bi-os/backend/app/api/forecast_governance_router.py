from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.schemas.forecast_governance import (
    GovernanceObjectSchema, EvaluateRequestSchema, EvaluationSchema,
    MonitoringSchema, DriftSchema, BenchmarkSchema, RetrainRequestSchema
)
from app.models.forecast_governance import (
    ModelGovernance, ForecastEvaluation, ForecastMonitoring, ForecastDrift, ModelBenchmark
)
from app.services.forecast_governance.evaluation_service import evaluation_service
from app.services.forecast_governance.drift_detector import drift_detector
from app.services.forecast_governance.monitor import forecast_monitor
from app.services.forecast_governance.governance_service import governance_service
from app.services.forecast_governance.lifecycle_manager import lifecycle_manager
from app.services.forecast_governance.benchmark_engine import benchmark_engine

router = APIRouter(prefix="/api/v1/forecast", tags=["forecast-governance"])

@router.post("/evaluate", response_model=EvaluationSchema)
def run_evaluation(req: EvaluateRequestSchema, db: Session = Depends(get_db)):
    metrics = evaluation_service.evaluate_forecast(req.actuals, req.predictions)
    
    # Ensure gov object exists
    gov = governance_service.get_or_create_governance(db, req.model_id, name=f"Model-{req.model_id}")
    
    eval_record = ForecastEvaluation(
        model_id=req.model_id,
        mae=metrics.get("mae"),
        rmse=metrics.get("rmse"),
        mape=metrics.get("mape"),
        smape=metrics.get("smape"),
        wmape=metrics.get("wmape"),
        mse=metrics.get("mse"),
        bias=metrics.get("bias"),
        forecast_error=metrics.get("forecast_error"),
        forecast_variance=metrics.get("forecast_variance"),
        prediction_coverage=metrics.get("prediction_coverage")
    )
    db.add(eval_record)
    db.commit()
    db.refresh(eval_record)
    
    # Compute new quality score
    governance_service.compute_quality_scores(db, req.model_id)
    
    return eval_record


@router.get("/evaluation", response_model=List[EvaluationSchema])
def get_evaluation(model_id: str, db: Session = Depends(get_db)):
    evals = db.query(ForecastEvaluation).filter(ForecastEvaluation.model_id == model_id).order_by(ForecastEvaluation.timestamp.desc()).all()
    return evals


@router.get("/monitoring", response_model=List[MonitoringSchema])
def get_monitoring(model_id: str, db: Session = Depends(get_db)):
    logs = db.query(ForecastMonitoring).filter(ForecastMonitoring.model_id == model_id).order_by(ForecastMonitoring.timestamp.desc()).all()
    return logs


@router.get("/drift", response_model=List[DriftSchema])
def get_drift(model_id: str, db: Session = Depends(get_db)):
    drifts = db.query(ForecastDrift).filter(ForecastDrift.model_id == model_id).order_by(ForecastDrift.timestamp.desc()).all()
    return drifts


@router.get("/benchmarks", response_model=List[BenchmarkSchema])
def get_benchmarks(model_id: str, db: Session = Depends(get_db)):
    benchmarks = db.query(ModelBenchmark).filter(ModelBenchmark.model_id == model_id).order_by(ModelBenchmark.timestamp.desc()).all()
    return benchmarks


@router.get("/governance", response_model=GovernanceObjectSchema)
def get_governance(model_id: str, db: Session = Depends(get_db)):
    gov = db.query(ModelGovernance).filter(ModelGovernance.model_id == model_id).first()
    if not gov:
        raise HTTPException(status_code=404, detail="Governance object not found")
    return gov


@router.post("/retrain")
def trigger_retrain(req: RetrainRequestSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Verify gov exists
    gov = db.query(ModelGovernance).filter(ModelGovernance.model_id == req.model_id).first()
    if not gov:
        raise HTTPException(status_code=404, detail="Governance object not found")
        
    # In a real system, we'd trigger a Celery task here. For now we just log a state transition.
    lifecycle_manager.transition_state(db, req.model_id, "Development", "System", f"Retrain triggered: {req.reason}")
    
    return {"status": "Retraining triggered", "model_id": req.model_id, "reason": req.reason}
