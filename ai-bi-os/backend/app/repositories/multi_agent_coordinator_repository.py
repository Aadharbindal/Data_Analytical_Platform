from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.models.multi_agent_coordinator import (
    AgentDefinition, WorkflowExecution, WorkflowNode, WorkflowDependency,
    WorkflowHistory, WorkflowMetrics, AgentHealth
)

class MultiAgentCoordinatorRepository:
    def __init__(self, db: Session):
        self.db = db

    # Agent Methods
    def create_agent(self, agent: AgentDefinition) -> AgentDefinition:
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def list_agents(self) -> List[AgentDefinition]:
        return self.db.query(AgentDefinition).all()

    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        return self.db.query(AgentDefinition).filter(AgentDefinition.id == agent_id).first()

    def get_agent_by_name(self, name: str) -> Optional[AgentDefinition]:
        return self.db.query(AgentDefinition).filter(AgentDefinition.name == name).first()

    # Workflow Methods
    def create_workflow(self, workflow: WorkflowExecution) -> WorkflowExecution:
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def update_workflow(self, workflow: WorkflowExecution) -> WorkflowExecution:
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowExecution]:
        return self.db.query(WorkflowExecution).filter(WorkflowExecution.id == workflow_id).first()

    def list_workflows(self, limit: int = 100) -> List[WorkflowExecution]:
        return self.db.query(WorkflowExecution).order_by(WorkflowExecution.started_at.desc()).limit(limit).all()

    # Node & Graph Methods
    def add_node(self, node: WorkflowNode) -> WorkflowNode:
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node
        
    def add_dependency(self, dep: WorkflowDependency):
        self.db.add(dep)
        self.db.commit()
        
    # Observability
    def add_history(self, history: WorkflowHistory):
        self.db.add(history)
        self.db.commit()

    def add_metric(self, metric: WorkflowMetrics):
        self.db.add(metric)
        self.db.commit()
