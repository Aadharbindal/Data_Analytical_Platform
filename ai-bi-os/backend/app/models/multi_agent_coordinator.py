from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Text, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class AgentDefinition(Base):
    """Registry metadata for a specialized agent (e.g., SQL Agent, Insight Engine)."""
    __tablename__ = "multi_agent_definitions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    version = Column(String, nullable=False, default="1.0.0")
    
    capabilities = Column(JSON, nullable=True) # Array of capabilities
    input_schema = Column(JSON, nullable=True) # JSONSchema defining what this agent requires
    output_schema = Column(JSON, nullable=True) # JSONSchema defining what this agent produces
    
    status = Column(String, nullable=False, default="ACTIVE") # ACTIVE, DEPRECATED, MAINTENANCE
    health = Column(String, nullable=False, default="HEALTHY") # HEALTHY, DEGRADED, DOWN

    created_at = Column(DateTime, default=datetime.utcnow)

class WorkflowExecution(Base):
    """The root object tracking a multi-agent orchestrated job."""
    __tablename__ = "multi_agent_workflow_executions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    
    request_payload = Column(JSON, nullable=False)
    unified_response = Column(JSON, nullable=True)
    
    status = Column(String, nullable=False, default="PENDING") # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    histories = relationship("WorkflowHistory", back_populates="workflow", cascade="all, delete-orphan")

class WorkflowNode(Base):
    """A specific execution step assigned to a registered agent."""
    __tablename__ = "multi_agent_workflow_nodes"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("multi_agent_workflow_executions.id", ondelete="CASCADE"))
    agent_id = Column(String, ForeignKey("multi_agent_definitions.id"))
    
    task_name = Column(String, nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    
    status = Column(String, nullable=False, default="PENDING") # PENDING, RUNNING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    workflow = relationship("WorkflowExecution", back_populates="nodes")
    agent = relationship("AgentDefinition")
    
    # We will simulate dependencies via the WorkflowDependency table

class WorkflowDependency(Base):
    """Edges of the DAG. node_id must wait for depends_on_node_id to complete."""
    __tablename__ = "multi_agent_workflow_dependencies"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("multi_agent_workflow_executions.id", ondelete="CASCADE"))
    
    node_id = Column(String, ForeignKey("multi_agent_workflow_nodes.id", ondelete="CASCADE"))
    depends_on_node_id = Column(String, ForeignKey("multi_agent_workflow_nodes.id", ondelete="CASCADE"))

class WorkflowHistory(Base):
    """Audit log of workflow state transitions."""
    __tablename__ = "multi_agent_workflow_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("multi_agent_workflow_executions.id", ondelete="CASCADE"))
    
    event = Column(String, nullable=False) # e.g. "NODE_COMPLETED", "AGGREGATION_STARTED"
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    workflow = relationship("WorkflowExecution", back_populates="histories")

class WorkflowMetrics(Base):
    """Observability metrics for DAG execution."""
    __tablename__ = "multi_agent_workflow_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    
    workflow_id = Column(String, nullable=False)
    total_latency_ms = Column(Integer, nullable=False)
    node_count = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)

class AgentHealth(Base):
    """Health telemetry for a specific agent."""
    __tablename__ = "multi_agent_health"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("multi_agent_definitions.id"))
    
    ping_latency_ms = Column(Integer, nullable=False)
    success_rate = Column(Float, nullable=False)
    failure_rate = Column(Float, nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)

class AgentAudit(Base):
    """Security audit log."""
    __tablename__ = "multi_agent_audit"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
