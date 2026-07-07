from sqlalchemy.orm import Session
from app.models.python_agent import (
    PythonWorkflow,
    PythonExecution,
    ExecutionArtifact,
    PythonAgentExecutionMetrics,
    PythonAgentExecutionHistory,
    ExecutionLog,
    ExecutionValidation
)
from typing import List, Optional
import json

class PythonExecutionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_workflow(self, workspace_id: str, intent: str, parameters: dict, steps: list) -> PythonWorkflow:
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

    def get_workflow(self, workflow_id: str) -> Optional[PythonWorkflow]:
        return self.db.query(PythonWorkflow).filter(PythonWorkflow.id == workflow_id).first()

    def create_execution(self, workflow_id: str) -> PythonExecution:
        execution = PythonExecution(
            workflow_id=workflow_id,
            status="PENDING"
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def update_execution_status(self, execution_id: str, status: str, error_message: str = None) -> PythonExecution:
        execution = self.db.query(PythonExecution).filter(PythonExecution.id == execution_id).first()
        if execution:
            execution.status = status
            if error_message:
                execution.error_message = error_message
            self.db.commit()
            self.db.refresh(execution)
            
            # Log history
            history = PythonAgentExecutionHistory(
                execution_id=execution_id,
                status_to=status
            )
            self.db.add(history)
            self.db.commit()
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

    def save_metrics(self, execution_id: str, execution_time_ms: int, peak_memory_mb: int, cpu_utilization: int) -> PythonAgentExecutionMetrics:
        metrics = PythonAgentExecutionMetrics(
            execution_id=execution_id,
            execution_time_ms=execution_time_ms,
            peak_memory_mb=peak_memory_mb,
            cpu_utilization=cpu_utilization
        )
        self.db.add(metrics)
        self.db.commit()
        self.db.refresh(metrics)
        return metrics
        
    def save_log(self, execution_id: str, trace: str) -> ExecutionLog:
        log = ExecutionLog(
            execution_id=execution_id,
            trace=trace
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def save_validation(self, execution_id: str, is_safe: bool, rejection_reason: str = None) -> ExecutionValidation:
        validation = ExecutionValidation(
            execution_id=execution_id,
            is_safe=is_safe,
            rejection_reason=rejection_reason
        )
        self.db.add(validation)
        self.db.commit()
        self.db.refresh(validation)
        return validation

    def get_execution(self, execution_id: str) -> Optional[PythonExecution]:
        return self.db.query(PythonExecution).filter(PythonExecution.id == execution_id).first()

    def get_executions_by_workspace(self, workspace_id: str) -> List[PythonExecution]:
        return self.db.query(PythonExecution).join(PythonWorkflow).filter(PythonWorkflow.workspace_id == workspace_id).order_by(PythonExecution.started_at.desc()).all()

    def get_artifacts(self, execution_id: str) -> List[ExecutionArtifact]:
        return self.db.query(ExecutionArtifact).filter(ExecutionArtifact.execution_id == execution_id).all()
