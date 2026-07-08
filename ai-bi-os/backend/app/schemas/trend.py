from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChangePointMeta(BaseModel):
    method: str
    type: str
    timestamp: str
    magnitude: float
    confidence: float

class TrendColumnRequest(BaseModel):
    name: str
    metric_name: Optional[str]
    total_observations: int
    signal_to_noise_ratio: float
    trend_stability: float
    start_val: float
    end_val: float
    has_growth: bool
    is_exponential: bool
    growth_rate: Optional[float]
    has_decline: bool
    decline_rate: Optional[float]
    momentum_score: float
    change_points: List[ChangePointMeta]

class RunTrendRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    columns: List[TrendColumnRequest]

class TrendRunResponse(BaseModel):
    run_id: str
    status: str
    series_processed: int
    execution_time_ms: float

class TrendSegmentSchema(BaseModel):
    trend_type: str
    trend_direction: str
    growth_rate: Optional[float]
    momentum_score: Optional[float]
    business_impact: Optional[str]

class ChangePointSchema(BaseModel):
    detection_method: str
    shift_type: str
    timestamp: str
    magnitude: float
    business_event_flag: bool

class TrendSummaryResponse(BaseModel):
    column_name: str
    overall_trend: str
    signal_to_noise_ratio: float
    increasing_segments: int
    decreasing_segments: int
    change_points_count: int
