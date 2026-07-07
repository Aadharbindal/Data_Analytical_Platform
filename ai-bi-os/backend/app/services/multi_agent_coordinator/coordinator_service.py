from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.multi_agent_coordinator import WorkflowExecution
from app.repositories.multi_agent_coordinator_repository import MultiAgentCoordinatorRepository
from app.schemas.multi_agent_coordinator import WorkflowExecuteRequest
from app.services.multi_agent_coordinator.task_planner import TaskPlanner
from app.services.multi_agent_coordinator.execution_graph import ExecutionGraphEngine

class MultiAgentCoordinatorService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = MultiAgentCoordinatorRepository(db)
        self.planner = TaskPlanner(db)
        self.executor = ExecutionGraphEngine(db)

    def execute_workflow(self, request: WorkflowExecuteRequest) -> WorkflowExecution:
        # 1. Initialize Workflow state
        workflow = WorkflowExecution(
            workspace_id=request.workspace_id,
            request_payload=request.request_payload
        )
        workflow = self.repository.create_workflow(workflow)
        
        # 2. Plan the Task DAG
        workflow = self.planner.plan(workflow)
        
        # 3. Execute the DAG (Synchronously in this mock, background queue in prod)
        workflow = self.executor.execute(workflow)
        
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowExecution]:
        return self.repository.get_workflow(workflow_id)

    def list_workflows(self) -> List[WorkflowExecution]:
        return self.repository.list_workflows()
