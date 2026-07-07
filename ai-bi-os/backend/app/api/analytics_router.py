from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.analytics.analytics_orchestrator import AnalyticsOrchestrator
from app.models.analytics import AnalyticsRun, AnalyticsBusinessMetric, InsightObject
from app.models.dataset import DatasetVersion, Dataset
from app.schemas.analytics import AnalyticsSummaryResponse, BusinessMetricSchema, InsightObjectSchema

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.post("/run")
def trigger_analytics_run(dataset_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually triggers an asynchronous analytics recalculation for a dataset."""
    version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.is_active == True).first()
    if not version:
        raise HTTPException(status_code=404, detail="Active dataset version not found")
        
    from app.worker import process_analytics_task
    process_analytics_task.delay(dataset_version_id=version.id)
    return {"status": "accepted", "message": "Analytics run queued"}

@router.get("/{dataset_id}", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(dataset_id: str, db: Session = Depends(get_db)):
    """Gets the status and summary of the latest analytics run."""
    version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.is_active == True).first()
    if not version:
        raise HTTPException(status_code=404, detail="Dataset version not found")
        
    run = db.query(AnalyticsRun).filter(AnalyticsRun.dataset_version_id == version.id).order_by(AnalyticsRun.started_at.desc()).first()
    if not run:
        raise HTTPException(status_code=404, detail="No analytics runs found for this dataset")
        
    return run

@router.get("/{dataset_id}/metrics", response_model=List[BusinessMetricSchema])
def get_analytics_metrics(dataset_id: str, db: Session = Depends(get_db)):
    """Gets the computed KPIs."""
    version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.is_active == True).first()
    if not version:
        raise HTTPException(status_code=404, detail="Dataset version not found")
        
    run = db.query(AnalyticsRun).filter(AnalyticsRun.dataset_version_id == version.id).order_by(AnalyticsRun.started_at.desc()).first()
    if not run:
        return []
        
    metrics = db.query(BusinessMetric).filter(BusinessMetric.run_id == run.id).all()
    return metrics

@router.get("/{dataset_id}/insights", response_model=List[InsightObjectSchema])
def get_analytics_insights(dataset_id: str, db: Session = Depends(get_db)):
    """Gets the structured insight objects."""
    version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.is_active == True).first()
    if not version:
        raise HTTPException(status_code=404, detail="Dataset version not found")
        
    run = db.query(AnalyticsRun).filter(AnalyticsRun.dataset_version_id == version.id).order_by(AnalyticsRun.started_at.desc()).first()
    if not run:
        return []
        
    insights = db.query(InsightObject).filter(InsightObject.run_id == run.id).all()
    return insights
