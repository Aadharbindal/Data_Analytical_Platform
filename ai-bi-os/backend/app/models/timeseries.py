"""
Module 27: Enterprise Time Series Analytics Engine — Database Models

Models:
- TimeSeriesRun
- TimeSeriesProfile
- FrequencyProfile
- WindowCalculation
- GapAnalysis
- TemporalValidation
- TimeSeriesHistory
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

class TimeSeriesRun(Base):
    """Core tracking entity for a time series analysis execution."""
    __tablename__ = "timeseries_runs"
    
    id = Column(String, primary_key=True, default=_uuid)
    dataset_id = Column(String, nullable=False, index=True)
    dataset_version_id = Column(String, nullable=False, index=True)
    
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    execution_time_ms = Column(Float, nullable=True)
    series_processed = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    profiles = relationship("TimeSeriesProfile", back_populates="run", cascade="all, delete-orphan")
    history = relationship("TimeSeriesHistory", back_populates="run", cascade="all, delete-orphan")

class TimeSeriesProfile(Base):
    """Profile of the temporal column."""
    __tablename__ = "timeseries_profiles"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("timeseries_runs.id"), nullable=False)
    
    column_name = Column(String, nullable=False)
    metric_name = Column(String, nullable=True) # What is being tracked (if explicitly mapped)
    
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    total_observations = Column(Integer, default=0)
    
    temporal_quality_score = Column(Float, nullable=True)
    temporal_completeness = Column(Float, nullable=True)
    temporal_consistency = Column(Float, nullable=True)
    
    run = relationship("TimeSeriesRun", back_populates="profiles")
    frequency = relationship("FrequencyProfile", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    gaps = relationship("GapAnalysis", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    windows = relationship("WindowCalculation", back_populates="profile", cascade="all, delete-orphan")
    validations = relationship("TemporalValidation", back_populates="profile", cascade="all, delete-orphan")

class FrequencyProfile(Base):
    """Detected frequency and consistency."""
    __tablename__ = "timeseries_frequency_profiles"
    
    id = Column(String, primary_key=True, default=_uuid)
    profile_id = Column(String, ForeignKey("timeseries_profiles.id"), nullable=False, unique=True)
    
    inferred_frequency = Column(String, nullable=True) # HOURLY, DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY, MIXED
    custom_interval_seconds = Column(Integer, nullable=True)
    
    frequency_confidence = Column(Float, nullable=True)
    
    profile = relationship("TimeSeriesProfile", back_populates="frequency")

class WindowCalculation(Base):
    """Stores executed rolling window limits."""
    __tablename__ = "timeseries_window_calculations"
    
    id = Column(String, primary_key=True, default=_uuid)
    profile_id = Column(String, ForeignKey("timeseries_profiles.id"), nullable=False)
    
    window_type = Column(String, nullable=False) # ROLLING_MEAN, ROLLING_SUM, EXPANDING_MAX
    window_size = Column(String, nullable=False) # e.g. "7D", "30D"
    
    # Store aggregated metadata (min, max, last_val) of the series over this window
    metadata_json = Column(JSON, nullable=True)
    
    profile = relationship("TimeSeriesProfile", back_populates="windows")

class GapAnalysis(Base):
    """Logs identified missing periods."""
    __tablename__ = "timeseries_gap_analysis"
    
    id = Column(String, primary_key=True, default=_uuid)
    profile_id = Column(String, ForeignKey("timeseries_profiles.id"), nullable=False, unique=True)
    
    missing_periods_count = Column(Integer, default=0)
    largest_gap_seconds = Column(Integer, nullable=True)
    
    continuity_score = Column(Float, nullable=True)
    coverage_score = Column(Float, nullable=True)
    
    # Array of {start: datetime, end: datetime, duration: seconds}
    gap_details = Column(JSON, nullable=True)
    
    profile = relationship("TimeSeriesProfile", back_populates="gaps")

class TemporalValidation(Base):
    """Records timezone consistency, order."""
    __tablename__ = "timeseries_validations"
    
    id = Column(String, primary_key=True, default=_uuid)
    profile_id = Column(String, ForeignKey("timeseries_profiles.id"), nullable=False)
    
    check_name = Column(String, nullable=False) # CHRONOLOGICAL_ORDER, DUPLICATES, TIMEZONE
    passed = Column(Boolean, nullable=False)
    details = Column(String, nullable=True)
    
    profile = relationship("TimeSeriesProfile", back_populates="validations")

class TimeSeriesHistory(Base):
    """Audit trail of the run."""
    __tablename__ = "timeseries_history"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("timeseries_runs.id"), nullable=False)
    
    action = Column(String, nullable=False) # STARTED, COMPLETED, FAILED
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("TimeSeriesRun", back_populates="history")
