from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Text, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class PythonWorkflow(Base):
    """The definition of the analytical steps to be executed."""
    __tablename__ = "py_workflows"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    
    intent = Column(String, nullable=False) # e.g., "Feature Engineering", "Clustering"
    parameters = Column(JSON, nullable=False) # Input datasets, columns, thresholds
    
    steps = Column(JSON, nullable=False) # DAG or linear sequence of deterministic analytical operations
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    executions = relationship("PythonExecution", back_populates="workflow", cascade="all, delete-orphan")

class PythonExecution(Base):
    """The runtime instance of a workflow."""
    __tablename__ = "py_executions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("py_workflows.id", ondelete="CASCADE"))
    
    status = Column(String, nullable=False, default="PENDING") # PENDING, VALIDATING, EXECUTING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    workflow = relationship("PythonWorkflow", back_populates="executions")
    artifacts = relationship("ExecutionArtifact", back_populates="execution", cascade="all, delete-orphan")
    metrics = relationship("ExecutionMetrics", uselist=False, back_populates="execution", cascade="all, delete-orphan")
    history = relationship("ExecutionHistory", back_populates="execution", cascade="all, delete-orphan")
    log = relationship("ExecutionLog", uselist=False, back_populates="execution", cascade="all, delete-orphan")
    validation = relationship("ExecutionValidation", uselist=False, back_populates="execution", cascade="all, delete-orphan")

class ExecutionArtifact(Base):
    """References to charts, tables, reports generated."""
    __tablename__ = "py_execution_artifacts"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    execution_id = Column(String, ForeignKey("py_executions.id", ondelete="CASCADE"))
    
    artifact_type = Column(String, nullable=False) # CHART, TABLE, REPORT, MODEL_METRICS
    name = Column(String, nullable=False)
    content_uri = Column(String, nullable=False) # Path to S3/Blob or inline JSON
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    execution = relationship("PythonExecution", back_populates="artifacts")

class ExecutionMetrics(Base):
    """Tracking CPU, memory, and latency."""
    __tablename__ = "py_execution_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    execution_id = Column(String, ForeignKey("py_executions.id", ondelete="CASCADE"), unique=True)
    
    execution_time_ms = Column(Integer, nullable=True)
    peak_memory_mb = Column(Integer, nullable=True)
    cpu_utilization = Column(Integer, nullable=True)
    
    execution = relationship("PythonExecution", back_populates="metrics")

class ExecutionHistory(Base):
    """State machine log for the execution."""
    __tablename__ = "py_execution_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    execution_id = Column(String, ForeignKey("py_executions.id", ondelete="CASCADE"))
    
    status_to = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    execution = relationship("PythonExecution", back_populates="history")

class ExecutionLog(Base):
    """Detailed outputs and traces."""
    __tablename__ = "py_execution_logs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    execution_id = Column(String, ForeignKey("py_executions.id", ondelete="CASCADE"), unique=True)
    
    trace = Column(Text, nullable=False)
    
    execution = relationship("PythonExecution", back_populates="log")

class ExecutionValidation(Base):
    """Records of safety and parameter checks."""
    __tablename__ = "py_execution_validations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    execution_id = Column(String, ForeignKey("py_executions.id", ondelete="CASCADE"), unique=True)
    
    is_safe = Column(Boolean, nullable=False)
    rejection_reason = Column(String, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    execution = relationship("PythonExecution", back_populates="validation")
