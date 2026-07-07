from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from app.schemas.recommendation_intelligence import (
    RecommendationGenerateRequest,
    RecommendationRegenerateRequest,
    RecommendationResponse,
    RecommendationListResponse,
    RecommendationSummaryResponse
)
from app.services.recommendation_intelligence.recommendation_manager import RecommendationManager

router = APIRouter(prefix="/recommendations-engine", tags=["recommendation-intelligence-engine"])

@router.post("/generate", response_model=RecommendationResponse)
def generate_recommendation(request: RecommendationGenerateRequest, db: Session = Depends(get_db)):
    manager = RecommendationManager(db)
    try:
        rec = manager.generate_recommendation(request)
        return rec
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspace/{workspace_id}", response_model=RecommendationListResponse)
def get_recommendations_by_workspace(workspace_id: str, db: Session = Depends(get_db)):
    manager = RecommendationManager(db)
    recs = manager.list_by_workspace(workspace_id)
    return RecommendationListResponse(recommendations=recs, total=len(recs))

@router.get("/dataset/{dataset_id}", response_model=RecommendationListResponse)
def get_recommendations_by_dataset(dataset_id: str, db: Session = Depends(get_db)):
    manager = RecommendationManager(db)
    recs = manager.repository.list_recommendations(dataset_id)
    return RecommendationListResponse(recommendations=recs, total=len(recs))

@router.get("/summary/{workspace_id}", response_model=RecommendationSummaryResponse)
def get_recommendation_summary(workspace_id: str, db: Session = Depends(get_db)):
    manager = RecommendationManager(db)
    summary = manager.get_summary(workspace_id)
    return RecommendationSummaryResponse(**summary)

@router.get("/{recommendation_id}", response_model=RecommendationResponse)
def get_recommendation(recommendation_id: str, db: Session = Depends(get_db)):
    manager = RecommendationManager(db)
    rec = manager.get_recommendation(recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return rec

@router.post("/regenerate", response_model=RecommendationResponse)
def regenerate_recommendation(request: RecommendationRegenerateRequest, db: Session = Depends(get_db)):
    manager = RecommendationManager(db)
    rec = manager.get_recommendation(request.recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return rec
    
@router.post("/archive")
def archive_recommendation(recommendation_id: str, db: Session = Depends(get_db)):
    manager = RecommendationManager(db)
    rec = manager.get_recommendation(recommendation_id)
    if rec:
        rec.status = "ARCHIVED"
        manager.repository.update_recommendation(rec)
    return {"status": "SUCCESS"}
