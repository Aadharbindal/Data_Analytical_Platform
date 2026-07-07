from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.insight import Insight
from app.models.dataset import DatasetVersion
from app.schemas.insight import InsightSchema

router = APIRouter(prefix="/api/v1/insights", tags=["insights"])

@router.get("", response_model=List[InsightSchema])
def get_insights(dataset_version_id: str = None, db: Session = Depends(get_db)):
    """Gets all insights for a dataset, sorted by rank/confidence."""
    query = db.query(Insight)
    if dataset_version_id:
        query = query.filter(Insight.dataset_version_id == dataset_version_id)
        
    insights = query.filter(Insight.status == "VALIDATED").all()
    
    # Sort by rank if available, otherwise by confidence
    insights.sort(
        key=lambda x: (
            x.ranking.final_score if x.ranking else 0,
            x.score.confidence if x.score else 0
        ),
        reverse=True
    )
    return insights


@router.post("/generate")
def trigger_insight_generation(run_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually triggers an asynchronous insight generation from an analytics run."""
    from app.worker import process_insight_task
    # In a full setup, we'd pass dataset_version_id or run_id
    # We will assume we can get dataset_version_id from the run
    from app.models.analytics import AnalyticsRun
    run = db.query(AnalyticsRun).filter(AnalyticsRun.id == run_id).first()
    if not run:
         raise HTTPException(status_code=404, detail="Analytics run not found")
         
    process_insight_task.delay(dataset_version_id=run.dataset_version_id)
    return {"status": "accepted", "message": "Insight generation queued"}

@router.get("/top", response_model=List[InsightSchema])
def get_top_insights(dataset_version_id: str, db: Session = Depends(get_db)):
    """Gets the highest ranked insights for a dataset."""
    insights = db.query(Insight).filter(
        Insight.dataset_version_id == dataset_version_id,
        Insight.status == "VALIDATED"
    ).all()
    
    # Sort by rank
    insights.sort(key=lambda x: x.ranking.final_score if x.ranking else 0, reverse=True)
    return insights[:10]

@router.get("/anomalies", response_model=List[InsightSchema])
def get_anomaly_insights(dataset_version_id: str, db: Session = Depends(get_db)):
    """Gets all insights categorized as ANOMALY or RISK."""
    insights = db.query(Insight).filter(
        Insight.dataset_version_id == dataset_version_id,
        Insight.status == "VALIDATED",
        Insight.category.in_(["ANOMALY", "RISK"])
    ).all()
    
    insights.sort(key=lambda x: x.ranking.final_score if x.ranking else 0, reverse=True)
    return insights
