from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class OutlierColumnRequest(BaseModel):
    name: str
    type: str
    valid_count: int
    mean: float
    median: float
    std_dev: float
    q1: float
    q3: float
    p99_9: float
    p00_1: float
    raw_values: List[float] # Mocked passing array

class RunOutlierRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    columns: List[OutlierColumnRequest]

class OutlierRunResponse(BaseModel):
    run_id: str
    status: str
    total_outliers: int
    execution_time_ms: float

class OutlierResultSchema(BaseModel):
    column_name: str
    row_reference: str
    detection_method: str
    severity: str
    outlier_type: str
    actual_value: float
    distance_from_mean: Optional[float]
    distance_from_median: Optional[float]
    business_impact: Optional[str]
    risk_score: Optional[float]

class ExtremeValueSchema(BaseModel):
    column_name: str
    extreme_type: str
    value: float
    tail_probability: float

class OutlierSummarySchema(BaseModel):
    column_name: Optional[str]
    total_outliers: int
    outlier_percentage: float
