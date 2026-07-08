from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class CalculateMetricRequest(BaseModel):
    metric_id: str
    dataset_version_id: str
    dimension: Optional[str] = None
    dimension_value: Optional[str] = None
    time_window: Optional[str] = None
    force_refresh: bool = False

class CalculateMetricResponse(BaseModel):
    metric_id: str
    value: Any # Could be float or dict if dimension split is requested
    cached: bool
    execution_time_ms: Optional[float] = None

class CreateMetricRequest(BaseModel):
    name: str
    domain: str
    description: Optional[str] = None
    formula: str
    supported_dimensions: Optional[List[str]] = []
    supported_time_windows: Optional[List[str]] = []
    author: Optional[str] = "system"

class MetricResponse(BaseModel):
    id: str
    name: str
    domain: str
    description: Optional[str]
    is_custom: bool
    supported_dimensions: List[str]
    supported_time_windows: List[str]
    formula: str

class MetricHistoryResponse(BaseModel):
    id: str
    metric_id: str
    action: str
    author: str
    timestamp: datetime
    changes: Optional[Dict[str, Any]]
