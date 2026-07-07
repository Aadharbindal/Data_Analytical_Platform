from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, Text, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class ToolRegistry(Base):
    """Central registry categorizing available tools for a workspace."""
    __tablename__ = "tl_registries"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    
    tools = relationship("ToolDefinition", back_populates="registry", cascade="all, delete-orphan")

class ToolDefinition(Base):
    """Definition of a deterministic backend tool's capabilities and schema."""
    __tablename__ = "tl_tool_definitions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    registry_id = Column(String, ForeignKey("tl_registries.id", ondelete="CASCADE"))
    
    tool_id_string = Column(String, nullable=False, unique=True) # e.g. "forecast.prophet.v1"
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=False) # Analytics, Dataset, Forecast, etc.
    version = Column(String, nullable=False, default="1.0.0")
    
    input_schema = Column(JSON, nullable=False) # JSON Schema definition
    output_schema = Column(JSON, nullable=False) # JSON Schema definition
    
    timeout_ms = Column(Integer, default=30000)
    retry_policy = Column(JSON, nullable=True) # e.g. {"max_retries": 3, "backoff": "exponential"}
    
    status = Column(String, nullable=False, default="ACTIVE") # ACTIVE, DEPRECATED, OFFLINE
    created_at = Column(DateTime, default=datetime.utcnow)
    
    registry = relationship("ToolRegistry", back_populates="tools")
    permissions = relationship("ToolPermission", back_populates="tool", cascade="all, delete-orphan")
    parameters = relationship("ToolParameter", back_populates="tool", cascade="all, delete-orphan")
    executions = relationship("ToolExecution", back_populates="tool")

class ToolPermission(Base):
    """RBAC restrictions mapped to specific tools."""
    __tablename__ = "tl_tool_permissions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    tool_id = Column(String, ForeignKey("tl_tool_definitions.id", ondelete="CASCADE"))
    
    role_required = Column(String, nullable=False)
    clearance_level = Column(Integer, default=1)
    
    tool = relationship("ToolDefinition", back_populates="permissions")

class ToolParameter(Base):
    """Deep validation rules beyond basic JSON schema (e.g. valid enum values, range constraints)."""
    __tablename__ = "tl_tool_parameters"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    tool_id = Column(String, ForeignKey("tl_tool_definitions.id", ondelete="CASCADE"))
    
    parameter_name = Column(String, nullable=False)
    validation_rules = Column(JSON, nullable=False) # e.g. {"min": 0, "max": 100, "regex": "^[a-z]+$"}
    
    tool = relationship("ToolDefinition", back_populates="parameters")

class ToolExecution(Base):
    """The runtime record of a specific tool invocation."""
    __tablename__ = "tl_tool_executions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    tool_id = Column(String, ForeignKey("tl_tool_definitions.id"), nullable=False)
    workflow_id = Column(String, nullable=True) # ID from AI Orchestrator
    
    input_parameters = Column(JSON, nullable=False)
    output = Column(JSON, nullable=True)
    
    status = Column(String, nullable=False, default="PENDING") # PENDING, EXECUTING, COMPLETED, FAILED, TIMEOUT
    error_details = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    tool = relationship("ToolDefinition", back_populates="executions")
    history = relationship("ToolExecutionHistory", back_populates="execution", cascade="all, delete-orphan")
    metrics = relationship("ToolMetrics", uselist=False, back_populates="execution", cascade="all, delete-orphan")
    audit = relationship("ToolAudit", uselist=False, back_populates="execution", cascade="all, delete-orphan")

class ToolExecutionHistory(Base):
    """State machine logging for executions."""
    __tablename__ = "tl_execution_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    execution_id = Column(String, ForeignKey("tl_tool_executions.id", ondelete="CASCADE"))
    
    status_from = Column(String, nullable=True)
    status_to = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    execution = relationship("ToolExecution", back_populates="history")

class ToolMetrics(Base):
    """Latency and health tracking."""
    __tablename__ = "tl_tool_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    execution_id = Column(String, ForeignKey("tl_tool_executions.id", ondelete="CASCADE"), unique=True)
    
    latency_ms = Column(Integer, nullable=True)
    is_success = Column(Boolean, default=False)
    
    execution = relationship("ToolExecution", back_populates="metrics")

class ToolAudit(Base):
    """Immutable log for execution security."""
    __tablename__ = "tl_tool_audits"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    execution_id = Column(String, ForeignKey("tl_tool_executions.id", ondelete="CASCADE"), unique=True)
    
    actor_id = Column(String, nullable=False) # Which agent or user invoked it
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    execution = relationship("ToolExecution", back_populates="audit")
