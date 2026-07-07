"""
Module 25: Enterprise Distribution Analytics Engine — Database Models

Models:
- DistributionRun
- DistributionProfile
- DistributionFit
- DistributionParameter
- GoodnessOfFitResult
- DensityProfile
- TailAnalysis
- DistributionHistory
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

class DistributionRun(Base):
    """Tracks execution metadata for a run."""
    __tablename__ = "distribution_runs"
    
    id = Column(String, primary_key=True, default=_uuid)
    dataset_id = Column(String, nullable=False, index=True)
    dataset_version_id = Column(String, nullable=False, index=True)
    
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    execution_time_ms = Column(Float, nullable=True)
    columns_processed = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    profiles = relationship("DistributionProfile", back_populates="run", cascade="all, delete-orphan")
    history = relationship("DistributionHistory", back_populates="run", cascade="all, delete-orphan")

class DistributionProfile(Base):
    """High-level profile of a column's distribution."""
    __tablename__ = "distribution_profiles"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("distribution_runs.id"), nullable=False)
    
    column_name = Column(String, nullable=False)
    column_type = Column(String, nullable=False) # NUMERICAL, CATEGORICAL
    
    mean = Column(Float, nullable=True)
    median = Column(Float, nullable=True)
    mode = Column(JSON, nullable=True)
    variance = Column(Float, nullable=True)
    std_dev = Column(Float, nullable=True)
    skewness = Column(Float, nullable=True)
    kurtosis = Column(Float, nullable=True)
    entropy = Column(Float, nullable=True)
    
    run = relationship("DistributionRun", back_populates="profiles")
    fits = relationship("DistributionFit", back_populates="profile", cascade="all, delete-orphan")
    density = relationship("DensityProfile", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    tail = relationship("TailAnalysis", back_populates="profile", uselist=False, cascade="all, delete-orphan")

class DistributionFit(Base):
    """The estimated best-fit distribution."""
    __tablename__ = "distribution_fits"
    
    id = Column(String, primary_key=True, default=_uuid)
    profile_id = Column(String, ForeignKey("distribution_profiles.id"), nullable=False)
    
    distribution_type = Column(String, nullable=False) # NORMAL, UNIFORM, POISSON...
    is_best_fit = Column(Boolean, default=False)
    fit_score = Column(Float, nullable=True)
    
    log_likelihood = Column(Float, nullable=True)
    aic = Column(Float, nullable=True)
    bic = Column(Float, nullable=True)
    
    profile = relationship("DistributionProfile", back_populates="fits")
    parameters = relationship("DistributionParameter", back_populates="fit", cascade="all, delete-orphan")
    gof_results = relationship("GoodnessOfFitResult", back_populates="fit", cascade="all, delete-orphan")

class DistributionParameter(Base):
    """Parameters for the fit (e.g. mean, std dev, alpha, beta)."""
    __tablename__ = "distribution_parameters"
    
    id = Column(String, primary_key=True, default=_uuid)
    fit_id = Column(String, ForeignKey("distribution_fits.id"), nullable=False)
    
    parameter_name = Column(String, nullable=False)
    parameter_value = Column(Float, nullable=False)
    
    fit = relationship("DistributionFit", back_populates="parameters")

class GoodnessOfFitResult(Base):
    """GOF test stats (KS, Shapiro, Chi-Square)."""
    __tablename__ = "goodness_of_fit_results"
    
    id = Column(String, primary_key=True, default=_uuid)
    fit_id = Column(String, ForeignKey("distribution_fits.id"), nullable=False)
    
    test_name = Column(String, nullable=False) # KS, SHAPIRO, CHI_SQUARE
    test_statistic = Column(Float, nullable=False)
    p_value = Column(Float, nullable=False)
    rejected = Column(Boolean, nullable=False)
    
    fit = relationship("DistributionFit", back_populates="gof_results")

class DensityProfile(Base):
    """Stores KDE and Histogram metadata."""
    __tablename__ = "density_profiles"
    
    id = Column(String, primary_key=True, default=_uuid)
    profile_id = Column(String, ForeignKey("distribution_profiles.id"), nullable=False, unique=True)
    
    kde_x = Column(JSON, nullable=True)
    kde_y = Column(JSON, nullable=True)
    
    histogram_bins = Column(JSON, nullable=True)
    histogram_counts = Column(JSON, nullable=True)
    
    profile = relationship("DistributionProfile", back_populates="density")

class TailAnalysis(Base):
    """Flags heavy tails, fat tails, multimodality."""
    __tablename__ = "tail_analysis"
    
    id = Column(String, primary_key=True, default=_uuid)
    profile_id = Column(String, ForeignKey("distribution_profiles.id"), nullable=False, unique=True)
    
    is_heavy_tail = Column(Boolean, default=False)
    is_long_tail = Column(Boolean, default=False)
    is_fat_tail = Column(Boolean, default=False)
    
    modality = Column(String, nullable=False) # UNIMODAL, BIMODAL, MULTIMODAL, FLAT
    tail_risk_score = Column(Float, nullable=True)
    
    profile = relationship("DistributionProfile", back_populates="tail")

class DistributionHistory(Base):
    """Audit trail of distribution analysis lifecycle."""
    __tablename__ = "distribution_history"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("distribution_runs.id"), nullable=False)
    
    action = Column(String, nullable=False) # STARTED, COMPLETED, FAILED
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("DistributionRun", back_populates="history")
