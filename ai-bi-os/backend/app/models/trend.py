"""
Module 28: Enterprise Trend & Change Detection Engine — Database Models

Models:
- TrendRun
- TrendProfile
- TrendResult
- ChangePoint
- TrendSummary
- TrendValidation
- TrendHistory
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

class TrendRun(Base):
    """Core tracking entity for a trend analysis execution."""
    __tablename__ = "trend_runs"
    
    id = Column(String, primary_key=True, default=_uuid)
    dataset_id = Column(String, nullable=False, index=True)
    dataset_version_id = Column(String, nullable=False, index=True)
    
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    execution_time_ms = Column(Float, nullable=True)
    series_processed = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    profiles = relationship("TrendProfile", back_populates="run", cascade="all, delete-orphan")
    summaries = relationship("TrendSummary", back_populates="run", cascade="all, delete-orphan")
    history = relationship("TrendHistory", back_populates="run", cascade="all, delete-orphan")

class TrendProfile(Base):
    """High-level profile of the column's overall temporal trend."""
    __tablename__ = "trend_profiles"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("trend_runs.id"), nullable=False)
    
    column_name = Column(String, nullable=False)
    metric_name = Column(String, nullable=True)
    
    overall_trend = Column(String, nullable=False) # INCREASING, DECREASING, STABLE, MIXED
    signal_to_noise_ratio = Column(Float, nullable=True)
    trend_stability = Column(Float, nullable=True)
    
    run = relationship("TrendRun", back_populates="profiles")
    segments = relationship("TrendResult", back_populates="profile", cascade="all, delete-orphan")
    change_points = relationship("ChangePoint", back_populates="profile", cascade="all, delete-orphan")
    validations = relationship("TrendValidation", back_populates="profile", cascade="all, delete-orphan")

class TrendResult(Base):
    """Detailed segments of trends."""
    __tablename__ = "trend_results"
    
    id = Column(String, primary_key=True, default=_uuid)
    profile_id = Column(String, ForeignKey("trend_profiles.id"), nullable=False)
    
    trend_type = Column(String, nullable=False) # LINEAR_GROWTH, EXPONENTIAL_GROWTH, DECAY, PLATEAU
    trend_direction = Column(String, nullable=False) # UP, DOWN, FLAT
    
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    growth_rate = Column(Float, nullable=True)
    momentum_score = Column(Float, nullable=True)
    trend_confidence = Column(Float, nullable=True)
    
    business_impact = Column(String, nullable=True)
    
    profile = relationship("TrendProfile", back_populates="segments")

class ChangePoint(Base):
    """Specific timestamped shifts."""
    __tablename__ = "trend_change_points"
    
    id = Column(String, primary_key=True, default=_uuid)
    profile_id = Column(String, ForeignKey("trend_profiles.id"), nullable=False)
    
    detection_method = Column(String, nullable=False) # CUSUM, VARIANCE_SHIFT, MAS
    shift_type = Column(String, nullable=False) # TREND_REVERSAL, STRUCTURAL_BREAK, LEVEL_CHANGE
    
    timestamp = Column(DateTime, nullable=False)
    magnitude = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    
    business_event_flag = Column(Boolean, default=False)
    
    profile = relationship("TrendProfile", back_populates="change_points")

class TrendSummary(Base):
    """Aggregated dataset-level trend insights."""
    __tablename__ = "trend_summaries"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("trend_runs.id"), nullable=False)
    
    column_name = Column(String, nullable=True)
    
    increasing_segments = Column(Integer, default=0)
    decreasing_segments = Column(Integer, default=0)
    total_change_points = Column(Integer, default=0)
    
    run = relationship("TrendRun", back_populates="summaries")

class TrendValidation(Base):
    """Records validation constraints."""
    __tablename__ = "trend_validations"
    
    id = Column(String, primary_key=True, default=_uuid)
    profile_id = Column(String, ForeignKey("trend_profiles.id"), nullable=False)
    
    check_name = Column(String, nullable=False) # MIN_WINDOW, NOISE_LEVEL
    passed = Column(Boolean, nullable=False)
    details = Column(String, nullable=True)
    
    profile = relationship("TrendProfile", back_populates="validations")

class TrendHistory(Base):
    """Audit trail of the run."""
    __tablename__ = "trend_history"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("trend_runs.id"), nullable=False)
    
    action = Column(String, nullable=False) # STARTED, COMPLETED, FAILED
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("TrendRun", back_populates="history")
