from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.python_agent import (
    PythonExecutionRequest,
    PythonValidationRequest,
    PythonExecutionResponse,
    ExecutionArtifactResponse
)
from app.repositories.python_agent import PythonExecutionRepository
from app.services.python_agent import PythonAgentService
from app.services.python_agent.python_agent_service import AnalysisValidator

router = APIRouter(prefix="/python", tags=["Python Analytics Agent"])

@router.post("/execute", response_model=PythonExecutionResponse)
def execute_workflow(request: PythonExecutionRequest, db: Session = Depends(get_db)):
    repo = PythonExecutionRepository(db)
    service = PythonAgentService(repo)
    
    execution = service.execute_workflow(
        workspace_id=request.workspace_id,
        workflow_def=request.workflow_definition
    )
    
    artifacts = []
    if execution.artifacts:
        for a in execution.artifacts:
            artifacts.append(ExecutionArtifactResponse(
                artifact_id=a.id,
                artifact_type=a.artifact_type,
                name=a.name,
                content_uri=a.content_uri
            ))
            
    metrics_time = execution.metrics.execution_time_ms if execution.metrics else None
    
    return PythonExecutionResponse(
        execution_id=execution.id,
        workflow_id=execution.workflow_id,
        status=execution.status,
        error_message=execution.error_message,
        execution_time_ms=metrics_time,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        artifacts=artifacts
    )

@router.post("/validate")
def validate_workflow(request: PythonValidationRequest):
    validator = AnalysisValidator()
    is_safe, reason = validator.validate(request.workflow_definition)
    return {
        "is_safe": is_safe,
        "reason": reason
    }

@router.get("/history/{workspace_id}", response_model=List[PythonExecutionResponse])
def get_execution_history(workspace_id: str, db: Session = Depends(get_db)):
    repo = PythonExecutionRepository(db)
    executions = repo.get_executions_by_workspace(workspace_id)
    
    res = []
    for execution in executions:
        metrics_time = execution.metrics.execution_time_ms if execution.metrics else None
        res.append(PythonExecutionResponse(
            execution_id=execution.id,
            workflow_id=execution.workflow_id,
            status=execution.status,
            error_message=execution.error_message,
            execution_time_ms=metrics_time,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            artifacts=[]
        ))
    return res

@router.get("/execution/{id}", response_model=PythonExecutionResponse)
def get_execution(id: str, db: Session = Depends(get_db)):
    repo = PythonExecutionRepository(db)
    execution = repo.get_execution(id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
        
    artifacts = []
    if execution.artifacts:
        for a in execution.artifacts:
            artifacts.append(ExecutionArtifactResponse(
                artifact_id=a.id,
                artifact_type=a.artifact_type,
                name=a.name,
                content_uri=a.content_uri
            ))
            
    metrics_time = execution.metrics.execution_time_ms if execution.metrics else None
    
    return PythonExecutionResponse(
        execution_id=execution.id,
        workflow_id=execution.workflow_id,
        status=execution.status,
        error_message=execution.error_message,
        execution_time_ms=metrics_time,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        artifacts=artifacts
    )

@router.get("/artifacts/{id}", response_model=List[ExecutionArtifactResponse])
def get_artifacts(id: str, db: Session = Depends(get_db)):
    repo = PythonExecutionRepository(db)
    artifacts = repo.get_artifacts(id)
    
    res = []
    for a in artifacts:
        res.append(ExecutionArtifactResponse(
            artifact_id=a.id,
            artifact_type=a.artifact_type,
            name=a.name,
            content_uri=a.content_uri
        ))
    return res

@router.post("/cancel/{id}")
def cancel_execution(id: str, db: Session = Depends(get_db)):
    repo = PythonExecutionRepository(db)
    execution = repo.get_execution(id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
        
    if execution.status in ["PENDING", "EXECUTING"]:
        repo.update_execution_status(id, "FAILED", "Cancelled by user")
        return {"status": "Cancelled"}
        
    return {"status": "Cannot cancel", "current_status": execution.status}
