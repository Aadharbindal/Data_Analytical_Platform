"""
Module 20: Enterprise Exploratory Data Analysis Engine — Database Models

Models:
- EDARun
- EDAProfile
- EDAColumnProfile
- DatasetSummary
- DistributionSummary
- MissingValueAnalysis
- OutlierCandidate
- EDAHistory
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

class EDARun(Base):
    """Top-level tracking of an EDA execution."""
    __tablename__ = "eda_runs"
    
    id = Column(String, primary_key=True, default=_uuid)
    dataset_id = Column(String, nullable=False, index=True)
    dataset_version_id = Column(String, nullable=False, index=True)
    
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    execution_time_ms = Column(Float, nullable=True)
    rows_processed = Column(Integer, default=0)
    columns_profiled = Column(Integer, default=0)
    
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    profile = relationship("EDAProfile", uselist=False, back_populates="run", cascade="all, delete-orphan")

class EDAProfile(Base):
    """Master profile linked to a run containing overall health scores and warnings."""
    __tablename__ = "eda_profiles"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("eda_runs.id"), nullable=False, unique=True)
    
    # Health Scores (0-100)
    completeness_score = Column(Float, nullable=True)
    consistency_score = Column(Float, nullable=True)
    usability_score = Column(Float, nullable=True)
    eda_quality_score = Column(Float, nullable=True)
    
    warnings = Column(JSON, nullable=True) # E.g. ["High cardinality in col X", "Many outliers in col Y"]
    
    run = relationship("EDARun", back_populates="profile")
    summary = relationship("DatasetSummary", uselist=False, back_populates="profile", cascade="all, delete-orphan")
    columns = relationship("EDAColumnProfile", back_populates="profile", cascade="all, delete-orphan")

class DatasetSummary(Base):
    """High-level dataset metrics."""
    __tablename__ = "eda_dataset_summaries"
    
    id = Column(String, primary_key=True, default=_uuid)
    profile_id = Column(String, ForeignKey("eda_profiles.id"), nullable=False, unique=True)
    
    total_rows = Column(Integer, default=0)
    total_columns = Column(Integer, default=0)
    dataset_size_bytes = Column(Integer, default=0)
    memory_usage_bytes = Column(Integer, default=0)
    
    numeric_columns = Column(Integer, default=0)
    categorical_columns = Column(Integer, default=0)
    date_columns = Column(Integer, default=0)
    boolean_columns = Column(Integer, default=0)
    text_columns = Column(Integer, default=0)
    
    profile = relationship("EDAProfile", back_populates="summary")

class EDAColumnProfile(Base):
    """Per-column statistics."""
    __tablename__ = "eda_column_profiles"
    
    id = Column(String, primary_key=True, default=_uuid)
    profile_id = Column(String, ForeignKey("eda_profiles.id"), nullable=False)
    
    column_name = Column(String, nullable=False)
    data_type = Column(String, nullable=False) # INTEGER, VARCHAR, DATE, BOOLEAN, etc.
    semantic_type = Column(String, nullable=True) # EMAIL, URL, PHONE, etc.
    business_type = Column(String, nullable=True) # IDENTIFIER, MEASURE, DIMENSION
    
    null_count = Column(Integer, default=0)
    null_percentage = Column(Float, default=0.0)
    distinct_count = Column(Integer, default=0)
    unique_ratio = Column(Float, default=0.0)
    cardinality = Column(String, nullable=True) # HIGH, MEDIUM, LOW
    duplicate_count = Column(Integer, default=0)
    duplicate_ratio = Column(Float, default=0.0)
    
    memory_usage_bytes = Column(Integer, default=0)
    storage_type = Column(String, nullable=True)
    
    # Polymorphic statistics depending on type
    numeric_stats = Column(JSON, nullable=True) # min, max, mean, median, mode, variance, std_dev, cv, skewness, kurtosis, percentiles, etc.
    categorical_stats = Column(JSON, nullable=True) # top/bottom categories, frequencies, entropy, mode, rare categories
    date_stats = Column(JSON, nullable=True) # min_date, max_date, time_span, missing_dates, duplicate_dates, granularity, seasonality_candidates, business_calendar
    text_stats = Column(JSON, nullable=True) # avg_length, max_length, min_length, vocab_size, character_dist, language, common_tokens, missing_text
    boolean_stats = Column(JSON, nullable=True) # true_count, false_count, true_ratio, false_ratio
    
    profile = relationship("EDAProfile", back_populates="columns")
    distribution = relationship("DistributionSummary", uselist=False, back_populates="column", cascade="all, delete-orphan")
    missing_analysis = relationship("MissingValueAnalysis", uselist=False, back_populates="column", cascade="all, delete-orphan")
    outliers = relationship("OutlierCandidate", back_populates="column", cascade="all, delete-orphan")

class DistributionSummary(Base):
    """Identified distribution types for numeric/date columns."""
    __tablename__ = "eda_distribution_summaries"
    
    id = Column(String, primary_key=True, default=_uuid)
    column_id = Column(String, ForeignKey("eda_column_profiles.id"), nullable=False, unique=True)
    
    distribution_type = Column(String, nullable=True) # NORMAL, UNIFORM, SKEWED, BIMODAL, HEAVY_TAIL, LONG_TAIL
    confidence_score = Column(Float, nullable=True)
    
    column = relationship("EDAColumnProfile", back_populates="distribution")

class MissingValueAnalysis(Base):
    """Missing value patterns."""
    __tablename__ = "eda_missing_value_analysis"
    
    id = Column(String, primary_key=True, default=_uuid)
    column_id = Column(String, ForeignKey("eda_column_profiles.id"), nullable=False, unique=True)
    
    missing_pattern = Column(String, nullable=True) # RANDOM, SEQUENTIAL, CHUNKED
    missing_percentage = Column(Float, default=0.0)
    
    column = relationship("EDAColumnProfile", back_populates="missing_analysis")

class OutlierCandidate(Base):
    """Rows/values flagged as potential outliers (not anomalies)."""
    __tablename__ = "eda_outlier_candidates"
    
    id = Column(String, primary_key=True, default=_uuid)
    column_id = Column(String, ForeignKey("eda_column_profiles.id"), nullable=False)
    
    method_used = Column(String, nullable=False) # IQR, Z_SCORE, MODIFIED_Z_SCORE
    value_flagged = Column(String, nullable=False) # The actual value as a string
    score = Column(Float, nullable=True) # e.g. the Z-score value
    
    column = relationship("EDAColumnProfile", back_populates="outliers")

class EDAHistory(Base):
    """Audit trail of execution times and failures."""
    __tablename__ = "eda_history"
    
    id = Column(String, primary_key=True, default=_uuid)
    dataset_version_id = Column(String, nullable=False, index=True)
    
    action = Column(String, nullable=False) # STARTED, COMPLETED, FAILED, CANCELLED
    execution_time_ms = Column(Float, nullable=True)
    errors = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
