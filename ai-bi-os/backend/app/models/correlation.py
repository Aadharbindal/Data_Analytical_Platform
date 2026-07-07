"""
Module 21: Enterprise Correlation & Association Analysis Engine — Database Models

Models:
- CorrelationRun
- CorrelationResult
- AssociationResult
- CorrelationMatrix
- FeatureRelationship
- CorrelationHistory
- CorrelationCache
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

class CorrelationRun(Base):
    """Top-level tracking of an Correlation execution."""
    __tablename__ = "correlation_runs"
    
    id = Column(String, primary_key=True, default=_uuid)
    dataset_id = Column(String, nullable=False, index=True)
    dataset_version_id = Column(String, nullable=False, index=True)
    
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    execution_time_ms = Column(Float, nullable=True)
    pairs_evaluated = Column(Integer, default=0)
    significant_relationships_found = Column(Integer, default=0)
    
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    numerical_results = relationship("CorrelationResult", back_populates="run", cascade="all, delete-orphan")
    association_results = relationship("AssociationResult", back_populates="run", cascade="all, delete-orphan")
    matrices = relationship("CorrelationMatrix", back_populates="run", cascade="all, delete-orphan")
    feature_relationships = relationship("FeatureRelationship", back_populates="run", cascade="all, delete-orphan")

class CorrelationResult(Base):
    """Stores individual pairwise numerical correlations (Pearson, Spearman)."""
    __tablename__ = "correlation_results"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("correlation_runs.id"), nullable=False)
    
    column_x = Column(String, nullable=False)
    column_y = Column(String, nullable=False)
    
    method_used = Column(String, nullable=False) # PEARSON, SPEARMAN, KENDALL
    coefficient = Column(Float, nullable=False)
    p_value = Column(Float, nullable=False)
    sample_size = Column(Integer, nullable=False)
    
    is_significant = Column(Boolean, default=False)
    strength_classification = Column(String, nullable=False) # Strong Positive, Weak Negative
    
    run = relationship("CorrelationRun", back_populates="numerical_results")

class AssociationResult(Base):
    """Stores categorical/mixed associations (Cramér's V, Point-Biserial)."""
    __tablename__ = "association_results"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("correlation_runs.id"), nullable=False)
    
    column_x = Column(String, nullable=False)
    column_y = Column(String, nullable=False)
    
    method_used = Column(String, nullable=False) # CRAMERS_V, POINT_BISERIAL, MUTUAL_INFO
    coefficient = Column(Float, nullable=False)
    p_value = Column(Float, nullable=True) # Cramér's V uses chi-square p-value
    sample_size = Column(Integer, nullable=False)
    
    is_significant = Column(Boolean, default=False)
    strength_classification = Column(String, nullable=False)
    
    run = relationship("CorrelationRun", back_populates="association_results")

class CorrelationMatrix(Base):
    """JSON blob storing the full nxn matrix for efficient retrieval."""
    __tablename__ = "correlation_matrices"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("correlation_runs.id"), nullable=False)
    
    matrix_type = Column(String, nullable=False) # NUMERIC, CATEGORICAL, MIXED
    data = Column(JSON, nullable=False)
    
    run = relationship("CorrelationRun", back_populates="matrices")

class FeatureRelationship(Base):
    """Business interpretation objects (highly correlated, multicollinear, independent)."""
    __tablename__ = "feature_relationships"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("correlation_runs.id"), nullable=False)
    
    source_metric = Column(String, nullable=False)
    target_metric = Column(String, nullable=False)
    
    relationship_type = Column(String, nullable=False) # HIGHLY_CORRELATED, REDUNDANT, INDEPENDENT
    business_relevance = Column(Text, nullable=True)
    supporting_statistics = Column(JSON, nullable=True)
    
    run = relationship("CorrelationRun", back_populates="feature_relationships")

class CorrelationHistory(Base):
    """Audit trail of calculation runs."""
    __tablename__ = "correlation_history"
    
    id = Column(String, primary_key=True, default=_uuid)
    dataset_version_id = Column(String, nullable=False, index=True)
    
    action = Column(String, nullable=False) # STARTED, COMPLETED, FAILED, CANCELLED
    execution_time_ms = Column(Float, nullable=True)
    errors = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class CorrelationCache(Base):
    """Metadata for caching mechanisms."""
    __tablename__ = "correlation_caches"
    
    id = Column(String, primary_key=True, default=_uuid)
    cache_key = Column(String, unique=True, index=True, nullable=False)
    dataset_version_id = Column(String, nullable=False)
    
    result_data = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_valid = Column(Boolean, default=True)
