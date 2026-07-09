from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class RunEDARequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    schema_info: List[Dict[str, str]] # [{'name': 'col1', 'type': 'NUMERIC'}]

class EDARunResponse(BaseModel):
    run_id: str
    status: str
    execution_time_ms: float

class DatasetSummaryResponse(BaseModel):
    total_rows: int
    total_columns: int
    dataset_size_bytes: int
    memory_usage_bytes: int
    numeric_columns: int
    categorical_columns: int
    date_columns: int
    boolean_columns: int
    text_columns: int

class DistributionResponse(BaseModel):
    type: str
    confidence: float

class OutlierResponse(BaseModel):
    method: str
    value: str
    score: float

class ColumnProfileResponse(BaseModel):
    column_name: str
    data_type: str
    null_count: int
    null_percentage: float
    distinct_count: int
    memory_usage_bytes: int
    specific_stats: Optional[Dict[str, Any]] = None
    distribution: Optional[DistributionResponse] = None
    outliers: Optional[List[OutlierResponse]] = None

class EDAProfileResponse(BaseModel):
    run_id: str
    completeness_score: float
    consistency_score: float
    usability_score: float
    eda_quality_score: float
    warnings: List[str]
    summary: DatasetSummaryResponse
    columns: List[ColumnProfileResponse]
