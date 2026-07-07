"""
Module 26: Enterprise Outlier & Extreme Value Analysis Engine — Database Models

Models:
- OutlierRun
- OutlierResult
- OutlierSummary
- ThresholdDefinition
- ExtremeValue
- OutlierValidation
- OutlierHistory
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

class OutlierRun(Base):
    """Core tracking entity for an outlier analysis execution."""
    __tablename__ = "outlier_runs"
    
    id = Column(String, primary_key=True, default=_uuid)
    dataset_id = Column(String, nullable=False, index=True)
    dataset_version_id = Column(String, nullable=False, index=True)
    
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    execution_time_ms = Column(Float, nullable=True)
    rows_processed = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    results = relationship("OutlierResult", back_populates="run", cascade="all, delete-orphan")
    summaries = relationship("OutlierSummary", back_populates="run", cascade="all, delete-orphan")
    extremes = relationship("ExtremeValue", back_populates="run", cascade="all, delete-orphan")
    history = relationship("OutlierHistory", back_populates="run", cascade="all, delete-orphan")
    validations = relationship("OutlierValidation", back_populates="run", cascade="all, delete-orphan")

class OutlierResult(Base):
    """Individual detected outlier record."""
    __tablename__ = "outlier_results"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("outlier_runs.id"), nullable=False)
    
    column_name = Column(String, nullable=False)
    row_reference = Column(String, nullable=True) # Row ID/Index
    
    detection_method = Column(String, nullable=False) # IQR, Z_SCORE, MAD
    severity = Column(String, nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    outlier_type = Column(String, nullable=False) # GLOBAL, LOCAL, CONTEXTUAL
    
    actual_value = Column(Float, nullable=False)
    distance_from_mean = Column(Float, nullable=True)
    distance_from_median = Column(Float, nullable=True)
    
    business_impact = Column(String, nullable=True) # Description of impact
    risk_score = Column(Float, nullable=True)
    
    run = relationship("OutlierRun", back_populates="results")

class OutlierSummary(Base):
    """Aggregated dataset/column-level summaries."""
    __tablename__ = "outlier_summaries"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("outlier_runs.id"), nullable=False)
    
    column_name = Column(String, nullable=True) # Null if dataset-level
    
    total_outliers = Column(Integer, default=0)
    outlier_percentage = Column(Float, default=0.0)
    
    severity_distribution = Column(JSON, nullable=True) # {"HIGH": 5, "LOW": 10}
    type_distribution = Column(JSON, nullable=True)
    
    run = relationship("OutlierRun", back_populates="summaries")

class ThresholdDefinition(Base):
    """Stores configured bounds or dynamic rules."""
    __tablename__ = "outlier_thresholds"
    
    id = Column(String, primary_key=True, default=_uuid)
    dataset_id = Column(String, nullable=False)
    column_name = Column(String, nullable=False)
    
    threshold_type = Column(String, nullable=False) # STATIC, DYNAMIC_IQR, DYNAMIC_Z
    upper_bound = Column(Float, nullable=True)
    lower_bound = Column(Float, nullable=True)
    
    multiplier = Column(Float, nullable=True) # e.g. 1.5 for IQR

class ExtremeValue(Base):
    """Specific model for Extreme Value Theory candidates."""
    __tablename__ = "outlier_extreme_values"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("outlier_runs.id"), nullable=False)
    column_name = Column(String, nullable=False)
    
    extreme_type = Column(String, nullable=False) # EXTREME_HIGH, EXTREME_LOW
    value = Column(Float, nullable=False)
    tail_probability = Column(Float, nullable=True) # EVT derived probability
    
    run = relationship("OutlierRun", back_populates="extremes")

class OutlierValidation(Base):
    """Logs validation checks (e.g., sample size rejections)."""
    __tablename__ = "outlier_validations"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("outlier_runs.id"), nullable=False)
    
    column_name = Column(String, nullable=False)
    check_name = Column(String, nullable=False) # MIN_SAMPLE_SIZE, SPARSITY
    passed = Column(Boolean, nullable=False)
    reason = Column(String, nullable=True)
    
    run = relationship("OutlierRun", back_populates="validations")

class OutlierHistory(Base):
    """Audit trail of the run."""
    __tablename__ = "outlier_history"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("outlier_runs.id"), nullable=False)
    
    action = Column(String, nullable=False) # STARTED, COMPLETED, FAILED
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("OutlierRun", back_populates="history")
