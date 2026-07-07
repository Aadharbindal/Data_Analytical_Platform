"""
Module 23: Enterprise Regression & Predictive Modeling Engine — Database Models

Models:
- RegressionModel
- RegressionRun
- RegressionResult
- FeatureImportance
- ResidualAnalysis
- Prediction
- ModelMetrics
- ModelVersion
- RegressionHistory
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

class RegressionModel(Base):
    """Core entity defining a trained model."""
    __tablename__ = "regression_models"
    
    id = Column(String, primary_key=True, default=_uuid)
    dataset_id = Column(String, nullable=False, index=True)
    
    name = Column(String, nullable=False)
    algorithm = Column(String, nullable=False) # LINEAR, RIDGE, LASSO, LOGISTIC
    target_variable = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")
    runs = relationship("RegressionRun", back_populates="model", cascade="all, delete-orphan")

class ModelVersion(Base):
    """Tracks iterative training, incremental updates, and rollbacks."""
    __tablename__ = "regression_model_versions"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("regression_models.id"), nullable=False)
    
    version_number = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    model = relationship("RegressionModel", back_populates="versions")

class RegressionRun(Base):
    """Tracks execution metadata for a training run."""
    __tablename__ = "regression_runs"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("regression_models.id"), nullable=False)
    dataset_version_id = Column(String, nullable=False)
    
    status = Column(String, default="PENDING") # PENDING, TRAINING, COMPLETED, FAILED
    execution_time_ms = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    model = relationship("RegressionModel", back_populates="runs")
    result = relationship("RegressionResult", back_populates="run", uselist=False, cascade="all, delete-orphan")
    metrics = relationship("ModelMetrics", back_populates="run", uselist=False, cascade="all, delete-orphan")
    feature_importance = relationship("FeatureImportance", back_populates="run", cascade="all, delete-orphan")
    residuals = relationship("ResidualAnalysis", back_populates="run", uselist=False, cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="run", cascade="all, delete-orphan")

class RegressionResult(Base):
    """Stores the trained parameters (intercept, coefficients)."""
    __tablename__ = "regression_results"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("regression_runs.id"), nullable=False, unique=True)
    
    intercept = Column(Float, nullable=False)
    coefficients = Column(JSON, nullable=False) # e.g. {"feature_1": 2.5, "feature_2": -1.2}
    
    run = relationship("RegressionRun", back_populates="result")

class ModelMetrics(Base):
    """Evaluation metrics for the model."""
    __tablename__ = "regression_metrics"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("regression_runs.id"), nullable=False, unique=True)
    
    r_squared = Column(Float, nullable=True)
    adjusted_r_squared = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    mse = Column(Float, nullable=True)
    aic = Column(Float, nullable=True)
    bic = Column(Float, nullable=True)
    
    run = relationship("RegressionRun", back_populates="metrics")

class FeatureImportance(Base):
    """Ranked list of features, standardized coefficients."""
    __tablename__ = "feature_importance"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("regression_runs.id"), nullable=False)
    
    feature_name = Column(String, nullable=False)
    importance_rank = Column(Integer, nullable=False)
    standardized_coefficient = Column(Float, nullable=False)
    p_value = Column(Float, nullable=True)
    vif = Column(Float, nullable=True) # Variance Inflation Factor
    
    run = relationship("RegressionRun", back_populates="feature_importance")

class ResidualAnalysis(Base):
    """Residual mean, variance, homoscedasticity indicators."""
    __tablename__ = "residual_analysis"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("regression_runs.id"), nullable=False, unique=True)
    
    residual_mean = Column(Float, nullable=False)
    residual_variance = Column(Float, nullable=False)
    
    normality_test_stat = Column(Float, nullable=True) # e.g. Shapiro-Wilk
    normality_p_value = Column(Float, nullable=True)
    
    homoscedasticity_test_stat = Column(Float, nullable=True) # e.g. Breusch-Pagan
    homoscedasticity_p_value = Column(Float, nullable=True)
    
    run = relationship("RegressionRun", back_populates="residuals")

class Prediction(Base):
    """Audit log of batch/single predictions made by the engine."""
    __tablename__ = "regression_predictions"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("regression_runs.id"), nullable=False)
    
    input_features = Column(JSON, nullable=False)
    predicted_value = Column(Float, nullable=False)
    confidence_lower = Column(Float, nullable=True)
    confidence_upper = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("RegressionRun", back_populates="predictions")

class RegressionHistory(Base):
    """Audit trail of model lifecycle."""
    __tablename__ = "regression_history"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("regression_models.id"), nullable=False)
    
    action = Column(String, nullable=False) # CREATED, TRAINED, RETRAINED, ROLLBACK
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
