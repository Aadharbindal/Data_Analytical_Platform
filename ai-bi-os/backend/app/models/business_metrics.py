"""
Module 19: Enterprise Business Metrics Engine — Database Models

Models:
- BusinessMetric
- MetricDefinition
- MetricFormula
- MetricCalculation
- MetricExecution
- MetricDependency
- MetricVersion
- MetricCache
- MetricHistory
"""

from sqlalchemy import (
    Column, String, Float, Boolean, ForeignKey,
    JSON, Integer, Text, DateTime, Enum as SAEnum
)
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from app.core.database import Base

def _uuid():
    return str(uuid.uuid4())

class MetricStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"

class BusinessMetric(Base):
    """Top-level representation of a metric."""
    __tablename__ = "business_metrics"
    
    id = Column(String, primary_key=True, default=_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, unique=True)
    domain = Column(String, nullable=False) # Sales, Marketing, Finance, etc.
    description = Column(Text, nullable=True)
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    versions = relationship("MetricVersion", back_populates="metric", cascade="all, delete-orphan")
    definitions = relationship("MetricDefinition", back_populates="metric", cascade="all, delete-orphan")

class MetricDefinition(Base):
    """Metadata and structure for the metric."""
    __tablename__ = "metric_definitions"
    
    id = Column(String, primary_key=True, default=_uuid)
    metric_id = Column(String, ForeignKey("business_metrics.id"), nullable=False)
    author = Column(String, nullable=True)
    supported_dimensions = Column(JSON, nullable=True) # ["Region", "Store", "Date"]
    supported_time_windows = Column(JSON, nullable=True) # ["Daily", "Monthly"]
    
    metric = relationship("BusinessMetric", back_populates="definitions")

class MetricVersion(Base):
    """Tracks versions, approvals, and rollback for a metric."""
    __tablename__ = "metric_versions"
    
    id = Column(String, primary_key=True, default=_uuid)
    metric_id = Column(String, ForeignKey("business_metrics.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    status = Column(SAEnum(MetricStatus), default=MetricStatus.DRAFT)
    activation_date = Column(DateTime, nullable=True)
    
    formula = relationship("MetricFormula", uselist=False, back_populates="version", cascade="all, delete-orphan")
    metric = relationship("BusinessMetric", back_populates="versions")

class MetricFormula(Base):
    """The actual calculation logic (e.g., arithmetic, conditionals)."""
    __tablename__ = "metric_formulas"
    
    id = Column(String, primary_key=True, default=_uuid)
    version_id = Column(String, ForeignKey("metric_versions.id"), nullable=False, unique=True)
    
    expression = Column(Text, nullable=False) # e.g. SUM(sales) / COUNT(customers)
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(JSON, nullable=True)
    
    version = relationship("MetricVersion", back_populates="formula")
    dependencies_out = relationship("MetricDependency", foreign_keys="MetricDependency.dependent_formula_id", back_populates="dependent_formula")

class MetricDependency(Base):
    """Adjacency list mapping derived metrics to root components."""
    __tablename__ = "metric_dependencies"
    
    id = Column(String, primary_key=True, default=_uuid)
    dependent_formula_id = Column(String, ForeignKey("metric_formulas.id"), nullable=False)
    depends_on_metric_id = Column(String, ForeignKey("business_metrics.id"), nullable=False)
    
    dependent_formula = relationship("MetricFormula", foreign_keys=[dependent_formula_id], back_populates="dependencies_out")
    depends_on_metric = relationship("BusinessMetric", foreign_keys=[depends_on_metric_id])

class MetricCalculation(Base):
    """Materialized results (value, slices/dimensions, time windows)."""
    __tablename__ = "metric_calculations"
    
    id = Column(String, primary_key=True, default=_uuid)
    metric_id = Column(String, ForeignKey("business_metrics.id"), nullable=False)
    dataset_version_id = Column(String, nullable=False, index=True)
    
    dimension = Column(String, nullable=True)
    dimension_value = Column(String, nullable=True)
    time_window = Column(String, nullable=True)
    
    value = Column(Float, nullable=False)
    previous_value = Column(Float, nullable=True)
    
    # Quality scores
    completeness_score = Column(Float, nullable=True)
    reliability_score = Column(Float, nullable=True)
    
    calculated_at = Column(DateTime, default=datetime.utcnow)

class MetricCache(Base):
    """Metadata for materialized query results (cache hit/miss logic)."""
    __tablename__ = "metric_caches"
    
    id = Column(String, primary_key=True, default=_uuid)
    cache_key = Column(String, unique=True, index=True, nullable=False)
    metric_id = Column(String, ForeignKey("business_metrics.id"), nullable=False)
    dataset_version_id = Column(String, nullable=False)
    
    result_value = Column(Float, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_valid = Column(Boolean, default=True)

class MetricExecution(Base):
    """Observability logs (execution time, failures)."""
    __tablename__ = "metric_executions"
    
    id = Column(String, primary_key=True, default=_uuid)
    metric_id = Column(String, ForeignKey("business_metrics.id"), nullable=False)
    execution_time_ms = Column(Float, nullable=False)
    was_cached = Column(Boolean, default=False)
    status = Column(String, default="SUCCESS")
    errors = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class MetricHistory(Base):
    """Audit trail for rollback and governance."""
    __tablename__ = "metric_history"
    
    id = Column(String, primary_key=True, default=_uuid)
    metric_id = Column(String, ForeignKey("business_metrics.id"), nullable=False)
    action = Column(String, nullable=False) # CREATED, ACTIVATED, DEPRECATED
    author = Column(String, nullable=True)
    changes = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
