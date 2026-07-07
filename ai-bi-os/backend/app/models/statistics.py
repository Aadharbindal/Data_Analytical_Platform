"""
Module 22: Enterprise Statistical Inference & Hypothesis Testing Engine — Database Models

Models:
- StatisticalRun
- HypothesisTest
- ConfidenceInterval
- DistributionProfile
- SamplingProfile
- InferenceResult
- ProbabilityResult
- InferenceHistory
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

class StatisticalRun(Base):
    """Top-level tracking of a statistical inference execution."""
    __tablename__ = "statistical_runs"
    
    id = Column(String, primary_key=True, default=_uuid)
    dataset_id = Column(String, nullable=False, index=True)
    dataset_version_id = Column(String, nullable=False, index=True)
    
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    execution_time_ms = Column(Float, nullable=True)
    total_tests_run = Column(Integer, default=0)
    significant_results_found = Column(Integer, default=0)
    
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    hypothesis_tests = relationship("HypothesisTest", back_populates="run", cascade="all, delete-orphan")
    confidence_intervals = relationship("ConfidenceInterval", back_populates="run", cascade="all, delete-orphan")
    stat_distribution_profiles = relationship("StatDistributionProfile", back_populates="run", cascade="all, delete-orphan")
    sampling_profiles = relationship("SamplingProfile", back_populates="run", cascade="all, delete-orphan")
    inference_results = relationship("InferenceResult", back_populates="run", cascade="all, delete-orphan")
    probability_results = relationship("ProbabilityResult", back_populates="run", cascade="all, delete-orphan")

class HypothesisTest(Base):
    """Stores specific hypothesis test results."""
    __tablename__ = "hypothesis_tests"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("statistical_runs.id"), nullable=False)
    
    test_name = Column(String, nullable=False) # T-TEST, ANOVA, CHI_SQUARE, MANN_WHITNEY
    target_metric = Column(String, nullable=False)
    grouping_variable = Column(String, nullable=True)
    
    test_statistic = Column(Float, nullable=False)
    p_value = Column(Float, nullable=False)
    degrees_of_freedom = Column(Float, nullable=True)
    
    alpha = Column(Float, default=0.05)
    reject_null_hypothesis = Column(Boolean, nullable=False)
    
    run = relationship("StatisticalRun", back_populates="hypothesis_tests")

class ConfidenceInterval(Base):
    """Stores bounds, margin of error, and confidence levels for metrics."""
    __tablename__ = "confidence_intervals"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("statistical_runs.id"), nullable=False)
    
    metric_name = Column(String, nullable=False)
    confidence_level = Column(Float, nullable=False) # 0.90, 0.95, 0.99
    
    lower_bound = Column(Float, nullable=False)
    upper_bound = Column(Float, nullable=False)
    margin_of_error = Column(Float, nullable=False)
    mean_estimate = Column(Float, nullable=False)
    
    run = relationship("StatisticalRun", back_populates="confidence_intervals")

class StatDistributionProfile(Base):
    """Stores the best-fit distribution parameters for a dataset column."""
    __tablename__ = "stat_distribution_profiles"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("statistical_runs.id"), nullable=False)
    
    column_name = Column(String, nullable=False)
    best_fit_distribution = Column(String, nullable=False) # NORMAL, POISSON, EXPONENTIAL, UNIFORM
    
    goodness_of_fit_test = Column(String, nullable=False) # SHAPIRO-WILK, K-S
    test_statistic = Column(Float, nullable=False)
    p_value = Column(Float, nullable=False)
    
    distribution_parameters = Column(JSON, nullable=True) # e.g. {"mu": 0, "sigma": 1}
    
    run = relationship("StatisticalRun", back_populates="stat_distribution_profiles")

class SamplingProfile(Base):
    """Tracks applied sampling methods and sample sizes."""
    __tablename__ = "sampling_profiles"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("statistical_runs.id"), nullable=False)
    
    sampling_method = Column(String, nullable=False) # RANDOM, STRATIFIED, BOOTSTRAP
    population_size = Column(Integer, nullable=False)
    sample_size = Column(Integer, nullable=False)
    
    strata_column = Column(String, nullable=True)
    confidence_level = Column(Float, nullable=True)
    margin_of_error_target = Column(Float, nullable=True)
    
    run = relationship("StatisticalRun", back_populates="sampling_profiles")

class InferenceResult(Base):
    """Stores high-level deterministic business interpretations."""
    __tablename__ = "inference_results"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("statistical_runs.id"), nullable=False)
    
    business_metric = Column(String, nullable=False)
    statistical_method = Column(String, nullable=False)
    
    significance_level = Column(String, nullable=False) # HIGHLY_SIGNIFICANT, SIGNIFICANT, NOT_SIGNIFICANT
    confidence_description = Column(String, nullable=False) 
    risk_level = Column(String, nullable=False) # LOW, MODERATE, HIGH
    
    supporting_statistics = Column(JSON, nullable=True)
    
    run = relationship("StatisticalRun", back_populates="inference_results")

class ProbabilityResult(Base):
    """Stores raw probability metrics (Alpha, Beta, Power)."""
    __tablename__ = "probability_results"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("statistical_runs.id"), nullable=False)
    
    test_name = Column(String, nullable=False)
    
    alpha = Column(Float, nullable=False)
    beta = Column(Float, nullable=True)
    statistical_power = Column(Float, nullable=True)
    effect_size = Column(Float, nullable=True)
    
    run = relationship("StatisticalRun", back_populates="probability_results")

class InferenceHistory(Base):
    """Audit trail of statistical runs."""
    __tablename__ = "inference_history"
    
    id = Column(String, primary_key=True, default=_uuid)
    dataset_version_id = Column(String, nullable=False, index=True)
    
    action = Column(String, nullable=False) # STARTED, COMPLETED, FAILED, CANCELLED
    execution_time_ms = Column(Float, nullable=True)
    errors = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
