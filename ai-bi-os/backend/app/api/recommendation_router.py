from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.recommendation import Recommendation
from app.models.dataset import DatasetVersion
from app.schemas.recommendation import RecommendationSchema

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])

@router.get("", response_model=List[RecommendationSchema])
def get_recommendations(dataset_version_id: str = None, db: Session = Depends(get_db)):
    """Gets all recommendations for a dataset, sorted by priority."""
    query = db.query(Recommendation)
    if dataset_version_id:
        query = query.filter(Recommendation.dataset_version_id == dataset_version_id)
        
    recs = query.filter(Recommendation.status != "REJECTED").all()
    
    def priority_score(rec):
        mapping = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        return mapping.get(rec.priority.upper(), 0)
        
    recs.sort(key=priority_score, reverse=True)
    return recs


@router.post("/generate")
def trigger_recommendation_generation(dataset_version_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually triggers recommendation generation from decisions."""
    from app.worker import process_recommendation_task
    
    version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Dataset version not found")
         
    process_recommendation_task.delay(dataset_version_id=dataset_version_id)
    return {"status": "accepted", "message": "Recommendation generation queued"}

@router.get("/high-priority", response_model=List[RecommendationSchema])
def get_high_priority_recommendations(dataset_version_id: str, db: Session = Depends(get_db)):
    """Gets the highest ranked recommendations."""
    recs = db.query(Recommendation).filter(
        Recommendation.dataset_version_id == dataset_version_id,
        Recommendation.status != "REJECTED"
    ).all()
    
    recs.sort(key=lambda x: x.score.final_score if x.score else 0, reverse=True)
    return recs[:10]

@router.get("/{recommendation_id}", response_model=RecommendationSchema)
def get_recommendation(recommendation_id: str, db: Session = Depends(get_db)):
    """Gets a specific recommendation with its full action plan."""
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return rec
