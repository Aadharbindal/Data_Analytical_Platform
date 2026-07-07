from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.multi_agent_coordinator import WorkflowExecution, WorkflowNode, WorkflowDependency
from app.repositories.multi_agent_coordinator_repository import MultiAgentCoordinatorRepository
from app.services.multi_agent_coordinator.agent_registry_service import AgentRegistryService

class TaskPlanner:
    """Parses a request and builds the Directed Acyclic Graph (DAG) for the workflow."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = MultiAgentCoordinatorRepository(db)
        self.registry = AgentRegistryService(db)

    def plan(self, workflow: WorkflowExecution) -> WorkflowExecution:
        payload = workflow.request_payload
        intent = payload.get("intent", "generic_query")
        
        # We simulate finding agents from registry. Fallback to mock ids if not found.
        sql_agent = self.registry.get_agent_by_name("SQL Analytics Agent")
        insight_agent = self.registry.get_agent_by_name("Insight Generation Engine")
        recommendation_agent = self.registry.get_agent_by_name("Recommendation Engine")
        
        sql_id = sql_agent.id if sql_agent else "mock-sql-id"
        insight_id = insight_agent.id if insight_agent else "mock-insight-id"
        rec_id = recommendation_agent.id if recommendation_agent else "mock-rec-id"

        # Construct nodes
        node_sql = WorkflowNode(
            workflow_id=workflow.id,
            agent_id=sql_id,
            task_name="Data Retrieval & SQL Execution",
            input_data={"query": payload.get("query")}
        )
        node_sql = self.repository.add_node(node_sql)

        node_insight = WorkflowNode(
            workflow_id=workflow.id,
            agent_id=insight_id,
            task_name="Insight Generation",
            input_data={"dependency": "SQL_RESULTS"}
        )
        node_insight = self.repository.add_node(node_insight)
        
        # Link DAG edges: Insight depends on SQL
        self.repository.add_dependency(WorkflowDependency(
            workflow_id=workflow.id,
            node_id=node_insight.id,
            depends_on_node_id=node_sql.id
        ))

        # If it's a deep analysis intent, we add recommendations
        if intent == "deep_analysis":
            node_rec = WorkflowNode(
                workflow_id=workflow.id,
                agent_id=rec_id,
                task_name="Recommendation Generation",
                input_data={"dependency": "INSIGHT_RESULTS"}
            )
            node_rec = self.repository.add_node(node_rec)
            
            # Recommendation depends on Insight
            self.repository.add_dependency(WorkflowDependency(
                workflow_id=workflow.id,
                node_id=node_rec.id,
                depends_on_node_id=node_insight.id
            ))
            
        return workflow
