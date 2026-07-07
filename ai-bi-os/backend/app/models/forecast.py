"""
Module 29: Enterprise Forecasting & Predictive Time Intelligence Engine — Database Models

Models:
- ForecastRun
- ForecastModel
- ForecastPrediction
- ForecastScenario
- ForecastAccuracy
- ForecastValidation
- ForecastHistory
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

class ForecastRun(Base):
    """Core tracking entity for a forecast execution."""
    __tablename__ = "forecast_runs"
    
    id = Column(String, primary_key=True, default=_uuid)
    dataset_id = Column(String, nullable=False, index=True)
    dataset_version_id = Column(String, nullable=False, index=True)
    
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    execution_time_ms = Column(Float, nullable=True)
    series_processed = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    models = relationship("ForecastModel", back_populates="run", cascade="all, delete-orphan")
    history = relationship("ForecastHistory", back_populates="run", cascade="all, delete-orphan")

class ForecastModel(Base):
    """Evaluated models for a metric, ranked by metrics."""
    __tablename__ = "forecast_models"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("forecast_runs.id"), nullable=False)
    
    column_name = Column(String, nullable=False)
    model_name = Column(String, nullable=False) # ARIMA, HOLT_WINTERS
    
    is_selected = Column(Boolean, default=False)
    
    aic = Column(Float, nullable=True)
    bic = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    
    run = relationship("ForecastRun", back_populates="models")
    predictions = relationship("ForecastPrediction", back_populates="model", cascade="all, delete-orphan")
    scenarios = relationship("ForecastScenario", back_populates="model", cascade="all, delete-orphan")
    accuracy = relationship("ForecastAccuracy", back_populates="model", cascade="all, delete-orphan")
    validations = relationship("ForecastValidation", back_populates="model", cascade="all, delete-orphan")

class ForecastPrediction(Base):
    """The actual serialized output predictions along the horizon."""
    __tablename__ = "forecast_predictions"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("forecast_models.id"), nullable=False)
    
    horizon_period = Column(String, nullable=False) # NEXT_DAY, NEXT_MONTH
    forecast_type = Column(String, nullable=True) # REVENUE, INVENTORY
    
    # Store predictions as a JSON array of {timestamp, expected_value, lower_bound, upper_bound}
    prediction_series = Column(JSON, nullable=False)
    
    confidence_level = Column(Float, default=95.0) # 95%
    
    model = relationship("ForecastModel", back_populates="predictions")

class ForecastScenario(Base):
    """Specific prediction bands mapped to a business context."""
    __tablename__ = "forecast_scenarios"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("forecast_models.id"), nullable=False)
    
    scenario_type = Column(String, nullable=False) # BASELINE, OPTIMISTIC, CONSERVATIVE
    business_impact_score = Column(Float, nullable=True)
    
    # Array of {timestamp, scenario_value}
    scenario_series = Column(JSON, nullable=False)
    
    model = relationship("ForecastModel", back_populates="scenarios")

class ForecastAccuracy(Base):
    """Backtesting and walk-forward validation outputs."""
    __tablename__ = "forecast_accuracy"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("forecast_models.id"), nullable=False, unique=True)
    
    rolling_backtest_rmse = Column(Float, nullable=True)
    walk_forward_mae = Column(Float, nullable=True)
    forecast_drift = Column(Float, nullable=True)
    
    model = relationship("ForecastModel", back_populates="accuracy")

class ForecastValidation(Base):
    """Records validation constraints."""
    __tablename__ = "forecast_validations"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("forecast_models.id"), nullable=False)
    
    check_name = Column(String, nullable=False) # STATIONARITY, SUFFICIENCY
    passed = Column(Boolean, nullable=False)
    details = Column(String, nullable=True)
    
    model = relationship("ForecastModel", back_populates="validations")

class ForecastHistory(Base):
    """Audit trail of the run."""
    __tablename__ = "forecast_history"
    
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("forecast_runs.id"), nullable=False)
    
    action = Column(String, nullable=False) # STARTED, COMPLETED, FAILED
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("ForecastRun", back_populates="history")
