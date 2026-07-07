from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class LifecycleSchema(BaseModel):
    status: str
    updated_by: Optional[str] = None
    notes: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class EvaluationSchema(BaseModel):
    timestamp: datetime
    mae: Optional[float] = None
    rmse: Optional[float] = None
    mape: Optional[float] = None
    smape: Optional[float] = None
    wmape: Optional[float] = None
    mse: Optional[float] = None
    bias: Optional[float] = None
    forecast_error: Optional[float] = None
    forecast_variance: Optional[float] = None
    prediction_coverage: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class MonitoringSchema(BaseModel):
    timestamp: datetime
    accuracy: Optional[float] = None
    drift_score: Optional[float] = None
    latency_ms: Optional[float] = None
    forecast_error: Optional[float] = None
    prediction_confidence: Optional[float] = None
    usage_count: int = 0
    failures_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class DriftSchema(BaseModel):
    timestamp: datetime
    data_drift_detected: bool = False
    feature_drift_detected: bool = False
    prediction_drift_detected: bool = False
    concept_drift_detected: bool = False
    performance_drift_detected: bool = False
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class BenchmarkSchema(BaseModel):
    timestamp: datetime
    naive_mae: Optional[float] = None
    naive_rmse: Optional[float] = None
    ma_mae: Optional[float] = None
    ma_rmse: Optional[float] = None
    historical_best_mae: Optional[float] = None
    historical_best_rmse: Optional[float] = None
    prod_model_mae: Optional[float] = None
    prod_model_rmse: Optional[float] = None
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AlertSchema(BaseModel):
    timestamp: datetime
    alert_type: str
    severity: str
    message: str
    is_resolved: bool

    model_config = ConfigDict(from_attributes=True)

class GovernanceObjectSchema(BaseModel):
    model_id: str
    forecast_id: Optional[str] = None
    name: str
    owner: Optional[str] = None
    version: str
    approval_status: str
    deployment_status: str
    quality_score: Optional[float] = None
    trust_score: Optional[float] = None
    
    lifecycle: List[LifecycleSchema] = []
    evaluations: List[EvaluationSchema] = []
    monitoring: List[MonitoringSchema] = []
    drifts: List[DriftSchema] = []
    benchmarks: List[BenchmarkSchema] = []
    alerts: List[AlertSchema] = []

    model_config = ConfigDict(from_attributes=True)

class EvaluateRequestSchema(BaseModel):
    model_id: str
    actuals: List[float]
    predictions: List[float]

class RetrainRequestSchema(BaseModel):
    model_id: str
    reason: str
