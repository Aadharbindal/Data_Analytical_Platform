from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from app.models.python_agent import (
    PythonWorkflow, PythonExecution, ExecutionArtifact,
    PythonAgentExecutionMetrics, PythonAgentExecutionHistory, ExecutionLog, ExecutionValidation
)

class PythonAgentRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_workflow(self, workspace_id: str, intent: str, parameters: Dict[str, Any], steps: List[Dict[str, Any]]) -> PythonWorkflow:
        workflow = PythonWorkflow(
            workspace_id=workspace_id,
            intent=intent,
            parameters=parameters,
            steps=steps
        )
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def create_execution(self, workflow_id: str) -> PythonExecution:
        execution = PythonExecution(workflow_id=workflow_id)
        self.db.add(execution)
        self.db.flush()
        
        history = PythonAgentExecutionHistory(
            execution_id=execution.id,
            status_to="PENDING"
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def update_execution(self, execution_id: str, status: str, error_message: str = None, execution_time_ms: int = None) -> PythonExecution:
        execution = self.db.query(PythonExecution).filter(PythonExecution.id == execution_id).first()
        if not execution:
            return None
            
        execution.status = status
        if error_message:
            execution.error_message = error_message
            
        if status in ["COMPLETED", "FAILED"]:
            execution.completed_at = datetime.utcnow()
            
            metrics = PythonAgentExecutionMetrics(
                execution_id=execution.id,
                execution_time_ms=execution_time_ms
            )
            self.db.add(metrics)
            
        self.db.add(execution)
        
        history = PythonAgentExecutionHistory(
            execution_id=execution.id,
            status_to=status
        )
        self.db.add(history)
        
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def save_artifact(self, execution_id: str, artifact_type: str, name: str, content_uri: str) -> ExecutionArtifact:
        artifact = ExecutionArtifact(
            execution_id=execution_id,
            artifact_type=artifact_type,
            name=name,
            content_uri=content_uri
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def save_validation(self, execution_id: str, is_safe: bool, rejection_reason: str = None) -> ExecutionValidation:
        validation = ExecutionValidation(
            execution_id=execution_id,
            is_safe=is_safe,
            rejection_reason=rejection_reason
        )
        self.db.add(validation)
        self.db.commit()
        return validation

    def save_log(self, execution_id: str, trace: str) -> ExecutionLog:
        log = ExecutionLog(
            execution_id=execution_id,
            trace=trace
        )
        self.db.add(log)
        self.db.commit()
        return log

    def get_execution(self, execution_id: str) -> Optional[PythonExecution]:
        return self.db.query(PythonExecution).filter(PythonExecution.id == execution_id).first()

    def get_history(self) -> List[PythonExecution]:
        return self.db.query(PythonExecution).order_by(desc(PythonExecution.started_at)).limit(100).all()

    def get_artifacts(self, execution_id: str) -> List[ExecutionArtifact]:
        return self.db.query(ExecutionArtifact).filter(ExecutionArtifact.execution_id == execution_id).all()
