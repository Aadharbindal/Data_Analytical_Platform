from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.repositories.orchestrator_repository import OrchestratorRepository
from app.schemas.orchestrator import (
    ExecutionRequest, ExecutionResponse,
    ExecutionPlanPayload, WorkflowTemplateResponse
)
from .execution_pipeline import ExecutionPipeline
from .task_scheduler import TaskScheduler
from .orchestrator_cache import orc_cache
from .workflow_planner import WorkflowPlanner
from .intent_router import IntentRouter

class OrchestratorService:
    def __init__(self, db: Session):
        self.repo = OrchestratorRepository(db)
        self.pipeline = ExecutionPipeline(self.repo)
        self.scheduler = TaskScheduler()
        self.planner = WorkflowPlanner()
        self.intent_router = IntentRouter()

    def execute_async(self, request: ExecutionRequest) -> ExecutionResponse:
        """
        Creates an execution context and queues it.
        Returns the initial state immediately (Accepted).
        """
        execution = self.repo.create_execution(request)
        
        # In a real setup, we'd do self.scheduler.schedule_execution(execution.id)
        # For our MVP backend, we'll run it synchronously so we can see state changes
        self.pipeline.run_pipeline(execution.id)
        
        # Refetch updated execution
        updated = self.repo.get_execution(execution.id)
        return ExecutionResponse.model_validate(updated)

    def plan_workflow(self, request: ExecutionRequest) -> ExecutionPlanPayload:
        """
        Dry-run / Dry-plan to show what the orchestrator would do.
        """
        intent_res = self.intent_router.classify_intent(request.user_request)
        plan = self.planner.build_plan(intent_res.intent, request.workspace_id)
        return plan

    def get_execution(self, execution_id: str) -> ExecutionResponse:
        execution = self.repo.get_execution(execution_id)
        if not execution:
            raise ValueError("Execution not found")
        return ExecutionResponse.model_validate(execution)

    def get_history(self) -> List[ExecutionResponse]:
        executions = self.repo.get_history()
        return [ExecutionResponse.model_validate(ex) for ex in executions]

    def get_workflows(self) -> List[WorkflowTemplateResponse]:
        workflows = self.repo.get_workflows()
        return [WorkflowTemplateResponse.model_validate(wf) for wf in workflows]

    def retry_execution(self, execution_id: str) -> ExecutionResponse:
        execution = self.repo.get_execution(execution_id)
        if not execution:
            raise ValueError("Execution not found")
        if execution.status not in ["FAILED", "COMPLETED"]:
            raise ValueError("Can only retry finished executions")
            
        self.repo.update_execution_status(execution_id, "RECEIVED", {"message": "Retry requested"})
        
        # Run synchronously for MVP
        self.pipeline.run_pipeline(execution_id)
        
        return ExecutionResponse.model_validate(self.repo.get_execution(execution_id))
