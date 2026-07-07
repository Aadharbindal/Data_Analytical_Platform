from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, Text, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def _uuid():
    return str(uuid.uuid4())

class ModelGovernance(Base):
    __tablename__ = "model_governance"
    
    id = Column(String, primary_key=True, default=_uuid)
    forecast_id = Column(String, index=True, nullable=True) # References the original ForecastRun or prediction job
    model_id = Column(String, index=True, nullable=False, unique=True) # References ForecastModel.id
    name = Column(String, nullable=False)
    owner = Column(String, nullable=True)
    version = Column(String, default="1.0.0")
    
    training_dataset_id = Column(String, nullable=True)
    dataset_version_id = Column(String, nullable=True)
    training_date = Column(DateTime, default=datetime.utcnow)
    
    approval_status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED
    deployment_status = Column(String, default="INACTIVE") # INACTIVE, STAGING, PRODUCTION
    
    quality_score = Column(Float, nullable=True)
    trust_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lifecycle = relationship("ModelLifecycle", back_populates="governance", cascade="all, delete-orphan")
    evaluations = relationship("ForecastEvaluation", back_populates="governance", cascade="all, delete-orphan")
    monitoring = relationship("ForecastMonitoring", back_populates="governance", cascade="all, delete-orphan")
    drifts = relationship("ForecastDrift", back_populates="governance", cascade="all, delete-orphan")
    benchmarks = relationship("ModelBenchmark", back_populates="governance", cascade="all, delete-orphan")
    alerts = relationship("ForecastAlert", back_populates="governance", cascade="all, delete-orphan")
    audits = relationship("ForecastAudit", back_populates="governance", cascade="all, delete-orphan")


class ModelLifecycle(Base):
    __tablename__ = "model_lifecycle"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("model_governance.model_id"), nullable=False)
    
    status = Column(String, nullable=False) # Development, Validation, Approved, Production, Deprecated, Retired
    updated_by = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    governance = relationship("ModelGovernance", back_populates="lifecycle")


class ForecastEvaluation(Base):
    __tablename__ = "forecast_evaluation"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("model_governance.model_id"), nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    mape = Column(Float, nullable=True)
    smape = Column(Float, nullable=True)
    wmape = Column(Float, nullable=True)
    mse = Column(Float, nullable=True)
    bias = Column(Float, nullable=True)
    forecast_error = Column(Float, nullable=True)
    forecast_variance = Column(Float, nullable=True)
    prediction_coverage = Column(Float, nullable=True)
    
    governance = relationship("ModelGovernance", back_populates="evaluations")


class ForecastMonitoring(Base):
    __tablename__ = "forecast_monitoring"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("model_governance.model_id"), nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    accuracy = Column(Float, nullable=True)
    drift_score = Column(Float, nullable=True)
    latency_ms = Column(Float, nullable=True)
    forecast_error = Column(Float, nullable=True)
    prediction_confidence = Column(Float, nullable=True)
    usage_count = Column(Integer, default=0)
    failures_count = Column(Integer, default=0)
    
    governance = relationship("ModelGovernance", back_populates="monitoring")


class ForecastDrift(Base):
    __tablename__ = "forecast_drift"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("model_governance.model_id"), nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    data_drift_detected = Column(Boolean, default=False)
    feature_drift_detected = Column(Boolean, default=False)
    prediction_drift_detected = Column(Boolean, default=False)
    concept_drift_detected = Column(Boolean, default=False)
    performance_drift_detected = Column(Boolean, default=False)
    
    details = Column(JSON, nullable=True)
    
    governance = relationship("ModelGovernance", back_populates="drifts")


class ModelBenchmark(Base):
    __tablename__ = "model_benchmark"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("model_governance.model_id"), nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    naive_mae = Column(Float, nullable=True)
    naive_rmse = Column(Float, nullable=True)
    ma_mae = Column(Float, nullable=True)
    ma_rmse = Column(Float, nullable=True)
    historical_best_mae = Column(Float, nullable=True)
    historical_best_rmse = Column(Float, nullable=True)
    prod_model_mae = Column(Float, nullable=True)
    prod_model_rmse = Column(Float, nullable=True)
    
    status = Column(String, nullable=True)
    
    governance = relationship("ModelGovernance", back_populates="benchmarks")


class ForecastAlert(Base):
    __tablename__ = "forecast_alert"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("model_governance.model_id"), nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    alert_type = Column(String, nullable=False) # ACCURACY_DROP, MODEL_DRIFT, FORECAST_FAILURE, CONFIDENCE_DROP, THRESHOLD_VIOLATION
    severity = Column(String, default="WARNING") # INFO, WARNING, CRITICAL
    message = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False)
    
    governance = relationship("ModelGovernance", back_populates="alerts")


class ForecastAudit(Base):
    __tablename__ = "forecast_audit"
    
    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("model_governance.model_id"), nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    action = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    user_id = Column(String, nullable=True)
    
    governance = relationship("ModelGovernance", back_populates="audits")
