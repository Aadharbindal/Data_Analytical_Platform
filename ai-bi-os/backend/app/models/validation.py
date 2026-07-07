"""
Module 24: Enterprise Confidence, Validation & Model Reliability Engine — Database Models

Models:
- ValidationRun
- ValidationResult
- ConfidenceScore
- ReliabilityScore
- ValidationPolicy
- ValidationRule
- ModelMonitoringRecord
- ValidationHistory
"""

from sqlalchemy import (
    Column, String, Float, Boolean, ForeignKey,
    JSON, Integer, Text, DateTime
)
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def _uuid():
    return str(uuid.uuid4())

class ValidationRun(Base):
    """Core tracking entity for a specific validation execution."""
    __tablename__ = "validation_runs"
    
    id = Column(String, primary_key=True, default=_uuid)
    target_object_id = Column(String, nullable=False, index=True) # e.g. KPI_ID, Model_ID
    target_object_type = Column(String, nullable=False) # KPI, REGRESSION, EDA, etc.
    
    status = Column(String, default="PENDING") # PENDING, IN_PROGRESS, COMPLETED, FAILED
    execution_time_ms = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    result = relationship("ValidationResult", back_populates="run", uselist=False, cascade="all, delete-orphan")
    confidence = relationship("ConfidenceScore", back_populates="run", uselist=False, cascade="all, delete-orphan")
    reliability = relationship("ReliabilityScore", back_populates="run", uselist=False, cascade="all, delete-orphan")
    history = relationship("ValidationHistory", back_populates="run", cascade="all, delete-orphan")

class ValidationResult(Base):
    """Final verdict and detailed feedback."""
    __tablename__ = "validation_results"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("validation_runs.id"), nullable=False, unique=True)
    
    validation_status = Column(String, nullable=False) # APPROVED, REJECTED, WARNING
    warnings = Column(JSON, nullable=True)
    errors = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    
    policy_version = Column(String, nullable=True)
    validator_version = Column(String, nullable=True)
    certification_timestamp = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("ValidationRun", back_populates="result")

class ConfidenceScore(Base):
    """Breakdown of Data, Statistical, Model, and Overall confidence."""
    __tablename__ = "validation_confidence_scores"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("validation_runs.id"), nullable=False, unique=True)
    
    overall_confidence = Column(Float, nullable=False) # 0-100
    statistical_confidence = Column(Float, nullable=True)
    data_confidence = Column(Float, nullable=True)
    model_confidence = Column(Float, nullable=True)
    business_confidence = Column(Float, nullable=True)
    prediction_confidence = Column(Float, nullable=True)
    
    confidence_level = Column(String, nullable=False) # HIGH, MEDIUM, LOW
    confidence_grade = Column(String, nullable=False) # A, B, C, D, F
    
    run = relationship("ValidationRun", back_populates="confidence")

class ReliabilityScore(Base):
    """Trust, Business Readiness, and Explainability scores."""
    __tablename__ = "validation_reliability_scores"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("validation_runs.id"), nullable=False, unique=True)
    
    reliability_score = Column(Float, nullable=False) # 0-100
    trust_score = Column(Float, nullable=False)
    business_readiness_score = Column(Float, nullable=False)
    production_readiness_score = Column(Float, nullable=False)
    explainability_score = Column(Float, nullable=False)
    
    run = relationship("ValidationRun", back_populates="reliability")

class ValidationPolicy(Base):
    """DB representation of an active policy threshold."""
    __tablename__ = "validation_policies"
    
    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False, unique=True)
    target_object_type = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    rules = relationship("ValidationRule", back_populates="policy", cascade="all, delete-orphan")

class ValidationRule(Base):
    """Specific rule components mapped to policies."""
    __tablename__ = "validation_rules"
    
    id = Column(String, primary_key=True, default=_uuid)
    policy_id = Column(String, ForeignKey("validation_policies.id"), nullable=False)
    
    metric_name = Column(String, nullable=False) # e.g. R_SQUARED, MISSING_PERCENTAGE
    operator = Column(String, nullable=False) # GREATER_THAN, LESS_THAN, EQUALS
    threshold_value = Column(Float, nullable=False)
    is_critical = Column(Boolean, default=True) # If true, violation = REJECTED, else WARNING
    
    policy = relationship("ValidationPolicy", back_populates="rules")

class ModelMonitoringRecord(Base):
    """Longitudinal tracking of drift, degradation, and accuracy."""
    __tablename__ = "model_monitoring_records"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, nullable=False, index=True)
    
    accuracy_trend = Column(Float, nullable=True)
    performance_degradation = Column(Float, nullable=True)
    data_drift_score = Column(Float, nullable=True)
    concept_drift_score = Column(Float, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)

class ValidationHistory(Base):
    """Audit trail of all validation events."""
    __tablename__ = "validation_history"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("validation_runs.id"), nullable=False)
    
    action = Column(String, nullable=False) # STARTED, COMPLETED, FAILED, POLICY_UPDATED
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("ValidationRun", back_populates="history")
