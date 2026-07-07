from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from app.schemas.insight_generation import (
    InsightGenerateRequest,
    InsightRegenerateRequest,
    InsightResponse,
    InsightListResponse,
    InsightSummaryResponse
)
from app.services.insight_generation.insight_manager import InsightManager

router = APIRouter(prefix="/insights-engine", tags=["insight-generation-engine"])

@router.post("/generate", response_model=InsightResponse)
def generate_insight(request: InsightGenerateRequest, db: Session = Depends(get_db)):
    manager = InsightManager(db)
    try:
        insight = manager.generate_insight(request)
        return insight
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspace/{workspace_id}", response_model=InsightListResponse)
def get_insights_by_workspace(workspace_id: str, db: Session = Depends(get_db)):
    manager = InsightManager(db)
    insights = manager.list_by_workspace(workspace_id)
    return InsightListResponse(insights=insights, total=len(insights))

@router.get("/dataset/{dataset_id}", response_model=InsightListResponse)
def get_insights_by_dataset(dataset_id: str, db: Session = Depends(get_db)):
    manager = InsightManager(db)
    insights = manager.repository.list_insights_by_dataset(dataset_id)
    return InsightListResponse(insights=insights, total=len(insights))

@router.get("/executive-summary/{workspace_id}", response_model=InsightSummaryResponse)
def get_executive_summary(workspace_id: str, db: Session = Depends(get_db)):
    manager = InsightManager(db)
    summary = manager.get_summary(workspace_id)
    return InsightSummaryResponse(**summary)

@router.get("/{insight_id}", response_model=InsightResponse)
def get_insight(insight_id: str, db: Session = Depends(get_db)):
    manager = InsightManager(db)
    insight = manager.get_insight(insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    return insight

@router.post("/regenerate", response_model=InsightResponse)
def regenerate_insight(request: InsightRegenerateRequest, db: Session = Depends(get_db)):
    # Stub for regeneration logic that would pass feedback to the orchestrator
    manager = InsightManager(db)
    insight = manager.get_insight(request.insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
        
    # Would normally re-run NarrativeGenerator here.
    return insight
