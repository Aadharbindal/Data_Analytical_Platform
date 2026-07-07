from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Text, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class ValidationObject(Base):
    """Core entity tracking the overall validation state of an AI output."""
    __tablename__ = "ai_validation_objects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    
    object_id = Column(String, nullable=False) # e.g. Insight ID, Recommendation ID
    object_type = Column(String, nullable=False) # INSIGHT, RECOMMENDATION, DECISION, SQL_RESULT, CHAT_RESPONSE
    
    validation_status = Column(String, nullable=False, default="PENDING") # PENDING, APPROVED, REJECTED
    
    confidence_score = Column(Float, nullable=False, default=0.0)
    evidence_score = Column(Float, nullable=False, default=0.0)
    policy_score = Column(Float, nullable=False, default=0.0)
    
    warnings = Column(JSON, nullable=True) # Array of warning strings
    errors = Column(JSON, nullable=True) # Array of error strings
    
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    
    results = relationship("AIValidationEngineResult", back_populates="validation", cascade="all, delete-orphan")
    histories = relationship("AIValidationEngineHistory", back_populates="validation", cascade="all, delete-orphan")

class AIValidationEngineResult(Base):
    """Detailed result of an individual validator check."""
    __tablename__ = "ai_validation_results"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    validation_id = Column(String, ForeignKey("ai_validation_objects.id", ondelete="CASCADE"))
    
    validator_name = Column(String, nullable=False) # FactChecker, EvidenceValidator, SchemaValidator, etc.
    status = Column(String, nullable=False) # PASS, FAIL, WARN, SKIPPED
    message = Column(Text, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    validation = relationship("ValidationObject", back_populates="results")

class AIValidationEngineRule(Base):
    """Configuration for what validators must pass."""
    __tablename__ = "ai_validation_rules"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    
    rule_name = Column(String, nullable=False)
    target_object_type = Column(String, nullable=False) # E.g., apply only to INSIGHTS
    
    validator_config = Column(JSON, nullable=False) # Specific thresholds, e.g. min_confidence = 0.85
    is_active = Column(Boolean, nullable=False, default=True)

class AIValidationEnginePolicy(Base):
    """Grouping of validation rules into a strict policy profile."""
    __tablename__ = "ai_validation_policies"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    policy_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    enforcement_level = Column(String, nullable=False, default="STRICT") # STRICT, LENIENT, AUDIT_ONLY

class AIValidationEngineHistory(Base):
    """Audit log of state transitions."""
    __tablename__ = "ai_validation_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    validation_id = Column(String, ForeignKey("ai_validation_objects.id", ondelete="CASCADE"))
    
    event = Column(String, nullable=False) # VALIDATION_STARTED, VALIDATOR_FAILED, REJECTED, APPROVED
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    validation = relationship("ValidationObject", back_populates="histories")

class ValidationMetrics(Base):
    """Observability metrics for pipeline execution."""
    __tablename__ = "ai_validation_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    
    validation_time_ms = Column(Integer, nullable=False)
    final_status = Column(String, nullable=False)
    object_type = Column(String, nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)

class ValidationAudit(Base):
    """Security audit log."""
    __tablename__ = "ai_validation_audit"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
