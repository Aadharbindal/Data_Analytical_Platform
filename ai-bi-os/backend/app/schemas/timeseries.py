from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class TimeSeriesColumnRequest(BaseModel):
    name: str
    metric_name: Optional[str]
    total_observations: int
    median_delta_seconds: Optional[int]
    frequency_confidence: Optional[float]
    missing_periods_count: Optional[int]
    largest_gap_seconds: Optional[int]
    coverage_score: Optional[float]
    is_strictly_ordered: Optional[bool]
    has_duplicates: Optional[bool]
    start_time: Optional[str]
    end_time: Optional[str]

class RunTimeSeriesRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    columns: List[TimeSeriesColumnRequest]

class TimeSeriesRunResponse(BaseModel):
    run_id: str
    status: str
    series_processed: int
    execution_time_ms: float

class TimeSeriesSummaryResponse(BaseModel):
    column_name: str
    metric_name: Optional[str]
    temporal_quality_score: float
    temporal_completeness: float
    inferred_frequency: Optional[str]
    continuity_score: Optional[float]
