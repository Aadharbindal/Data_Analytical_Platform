from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from app.core.database import get_db
from app.schemas.ai_evaluation_engine import (
    BenchmarkRequest,
    EvaluationResponse,
    LeaderboardResponse,
    RegressionReportResponse,
    EvaluationListResponse
)
from app.services.ai_evaluation_engine.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluation", tags=["ai-evaluation-engine"])

@router.post("/benchmark", response_model=EvaluationResponse)
def run_benchmark(request: BenchmarkRequest, db: Session = Depends(get_db)):
    service = EvaluationService(db)
    try:
        eval_obj = service.run_benchmark(request)
        return eval_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=EvaluationListResponse)
def get_evaluation_history(db: Session = Depends(get_db)):
    service = EvaluationService(db)
    evals = service.list_evaluations()
    return EvaluationListResponse(evaluations=evals, total=len(evals))

@router.get("/leaderboards/{workspace_id}", response_model=Dict[str, List[LeaderboardResponse]])
def get_leaderboards(workspace_id: str, db: Session = Depends(get_db)):
    service = EvaluationService(db)
    return service.get_leaderboards(workspace_id)

@router.get("/regressions/{workspace_id}", response_model=List[RegressionReportResponse])
def get_regressions(workspace_id: str, db: Session = Depends(get_db)):
    service = EvaluationService(db)
    return service.get_regressions(workspace_id)
