from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.schemas.orchestrator import (
    ExecutionRequest, ExecutionResponse,
    ExecutionPlanPayload, WorkflowTemplateResponse
)
from app.services.orchestrator import OrchestratorService

router = APIRouter(prefix="/orchestrator", tags=["AI Orchestrator Engine"])

@router.post("/execute", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
def execute_workflow(request: ExecutionRequest, db: Session = Depends(get_db)):
    service = OrchestratorService(db)
    return service.execute_async(request)

@router.post("/plan", response_model=ExecutionPlanPayload)
def plan_workflow(request: ExecutionRequest, db: Session = Depends(get_db)):
    service = OrchestratorService(db)
    return service.plan_workflow(request)

@router.get("/execution/{execution_id}", response_model=ExecutionResponse)
def get_execution(execution_id: str, db: Session = Depends(get_db)):
    service = OrchestratorService(db)
    try:
        return service.get_execution(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/history", response_model=List[ExecutionResponse])
def get_history(db: Session = Depends(get_db)):
    service = OrchestratorService(db)
    return service.get_history()

@router.get("/workflows", response_model=List[WorkflowTemplateResponse])
def get_workflows(db: Session = Depends(get_db)):
    service = OrchestratorService(db)
    return service.get_workflows()

@router.post("/retry", response_model=ExecutionResponse)
def retry_execution(execution_id: str, db: Session = Depends(get_db)):
    service = OrchestratorService(db)
    try:
        return service.retry_execution(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
