from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, Text, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class WorkflowTemplate(Base):
    """Pre-defined complex multi-agent flows."""
    __tablename__ = "orc_workflow_templates"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    steps = Column(JSON, nullable=False) # Graph of required steps
    
    is_active = Column(Boolean, default=True)

class WorkflowDefinition(Base):
    """Specific instantiated version of a workflow template for an execution."""
    __tablename__ = "orc_workflow_definitions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    template_id = Column(String, ForeignKey("orc_workflow_templates.id", ondelete="SET NULL"), nullable=True)
    
    workspace_id = Column(String, nullable=False)
    configuration = Column(JSON, nullable=False) # Specific variables/overrides
    
    template = relationship("WorkflowTemplate")

class AIExecution(Base):
    """The core record of an AI request's lifecycle."""
    __tablename__ = "orc_executions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    conversation_id = Column(String, nullable=True, index=True)
    workflow_id = Column(String, ForeignKey("orc_workflow_definitions.id"), nullable=True)
    
    user_request = Column(Text, nullable=False)
    detected_intent = Column(String, nullable=True)
    intent_confidence = Column(Float, nullable=True)
    
    selected_agent = Column(String, nullable=True)
    selected_model = Column(String, nullable=True)
    
    status = Column(String, nullable=False, default="RECEIVED") # RECEIVED, PLANNING, ROUTING, EXECUTING, VALIDATING, COMPLETED, FAILED
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    workflow = relationship("WorkflowDefinition")
    plan = relationship("ExecutionPlan", uselist=False, back_populates="execution", cascade="all, delete-orphan")
    history = relationship("ExecutionHistory", back_populates="execution", cascade="all, delete-orphan")
    metrics = relationship("ExecutionMetrics", uselist=False, back_populates="execution", cascade="all, delete-orphan")
    audit = relationship("ExecutionAudit", back_populates="execution", cascade="all, delete-orphan")

class ExecutionPlan(Base):
    """The structured graph of steps to fulfill the request."""
    __tablename__ = "orc_execution_plans"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    execution_id = Column(String, ForeignKey("orc_executions.id", ondelete="CASCADE"), unique=True)
    
    required_context = Column(JSON, nullable=True)
    required_evidence = Column(JSON, nullable=True)
    required_prompt = Column(JSON, nullable=True)
    required_tools = Column(JSON, nullable=True)
    
    validation_rules = Column(JSON, nullable=True)
    output_format = Column(String, nullable=True)
    
    execution = relationship("AIExecution", back_populates="plan")
    steps = relationship("ExecutionStep", back_populates="plan", cascade="all, delete-orphan")

class ExecutionStep(Base):
    """Individual step within a plan."""
    __tablename__ = "orc_execution_steps"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    plan_id = Column(String, ForeignKey("orc_execution_plans.id", ondelete="CASCADE"))
    
    step_name = Column(String, nullable=False)
    step_order = Column(Integer, nullable=False)
    
    status = Column(String, nullable=False, default="PENDING") # PENDING, IN_PROGRESS, COMPLETED, FAILED
    result = Column(JSON, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    plan = relationship("ExecutionPlan", back_populates="steps")

class ExecutionHistory(Base):
    """Immutable log of state changes for the execution."""
    __tablename__ = "orc_execution_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    execution_id = Column(String, ForeignKey("orc_executions.id", ondelete="CASCADE"))
    
    status_from = Column(String, nullable=True)
    status_to = Column(String, nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, nullable=True)
    
    execution = relationship("AIExecution", back_populates="history")

class ExecutionMetrics(Base):
    """Latency, cost, token usage tracking."""
    __tablename__ = "orc_execution_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    execution_id = Column(String, ForeignKey("orc_executions.id", ondelete="CASCADE"), unique=True)
    
    latency_ms = Column(Integer, nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    estimated_cost = Column(Float, default=0.0)
    retries_count = Column(Integer, default=0)
    
    execution = relationship("AIExecution", back_populates="metrics")

class ExecutionPolicy(Base):
    """Rules governing timeouts, fallbacks, and retries."""
    __tablename__ = "orc_execution_policies"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    
    max_retries = Column(Integer, default=3)
    timeout_ms = Column(Integer, default=30000)
    fallback_models = Column(JSON, nullable=True) # e.g. ["gpt-3.5-turbo", "gemini-flash"]
    graceful_degradation = Column(Boolean, default=True)

class ExecutionAudit(Base):
    """Security tracking."""
    __tablename__ = "orc_execution_audits"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    execution_id = Column(String, ForeignKey("orc_executions.id", ondelete="CASCADE"))
    
    user_id = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    execution = relationship("AIExecution", back_populates="audit")
