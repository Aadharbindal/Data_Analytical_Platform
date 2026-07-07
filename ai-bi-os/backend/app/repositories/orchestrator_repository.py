from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.models.orchestrator import (
    AIExecution, ExecutionPlan, ExecutionStep,
    ExecutionHistory, ExecutionMetrics, WorkflowTemplate
)
from app.schemas.orchestrator import ExecutionRequest
from datetime import datetime

class OrchestratorRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_execution(self, req: ExecutionRequest) -> AIExecution:
        execution = AIExecution(
            workspace_id=req.workspace_id,
            conversation_id=req.conversation_id,
            user_request=req.user_request,
            workflow_id=req.workflow_id
        )
        self.db.add(execution)
        self.db.flush()
        
        history = ExecutionHistory(
            execution_id=execution.id,
            status_to="RECEIVED",
            details={"message": "Execution initialized"}
        )
        self.db.add(history)
        
        metrics = ExecutionMetrics(execution_id=execution.id)
        self.db.add(metrics)
        
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def update_execution_status(self, execution_id: str, status: str, details: Dict[str, Any] = None):
        execution = self.db.query(AIExecution).filter(AIExecution.id == execution_id).first()
        if not execution:
            return
            
        old_status = execution.status
        execution.status = status
        if status in ["COMPLETED", "FAILED"]:
            execution.completed_at = datetime.utcnow()
            
        self.db.add(execution)
        
        history = ExecutionHistory(
            execution_id=execution.id,
            status_from=old_status,
            status_to=status,
            details=details
        )
        self.db.add(history)
        self.db.commit()

    def update_execution_intent(self, execution_id: str, intent: str, confidence: float):
        execution = self.db.query(AIExecution).filter(AIExecution.id == execution_id).first()
        if execution:
            execution.detected_intent = intent
            execution.intent_confidence = confidence
            self.db.add(execution)
            self.db.commit()

    def save_plan(self, execution_id: str, plan_payload: Dict[str, Any]):
        plan = ExecutionPlan(
            execution_id=execution_id,
            required_context=plan_payload.get("required_context"),
            required_evidence=plan_payload.get("required_evidence"),
            required_prompt=plan_payload.get("required_prompt"),
            required_tools=plan_payload.get("required_tools"),
            validation_rules=plan_payload.get("validation_rules"),
            output_format=plan_payload.get("output_format")
        )
        self.db.add(plan)
        self.db.flush()
        
        for step in plan_payload.get("steps", []):
            db_step = ExecutionStep(
                plan_id=plan.id,
                step_name=step["step_name"],
                step_order=step["step_order"]
            )
            self.db.add(db_step)
            
        self.db.commit()

    def get_execution(self, execution_id: str) -> Optional[AIExecution]:
        return self.db.query(AIExecution).options(
            joinedload(AIExecution.plan).joinedload(ExecutionPlan.steps),
            joinedload(AIExecution.metrics)
        ).filter(AIExecution.id == execution_id).first()

    def get_history(self) -> List[AIExecution]:
        return self.db.query(AIExecution).order_by(desc(AIExecution.created_at)).limit(100).all()

    def get_workflows(self) -> List[WorkflowTemplate]:
        return self.db.query(WorkflowTemplate).filter(WorkflowTemplate.is_active == True).all()
