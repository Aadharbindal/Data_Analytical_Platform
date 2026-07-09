from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class CandidateModelRequest(BaseModel):
    model_name: str
    aic: Optional[float]
    bic: Optional[float]
    rmse: float
    mae: float
    horizon_period: str
    forecast_type: str
    last_known_value: float

class ForecastMetricRequest(BaseModel):
    column_name: str
    is_stationary: bool
    total_observations: int
    candidate_models: List[CandidateModelRequest]

class RunForecastRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    metrics: List[ForecastMetricRequest]

class ForecastRunResponse(BaseModel):
    run_id: str
    status: str
    series_processed: int
    execution_time_ms: float

class PredictionPointSchema(BaseModel):
    timestamp: str
    expected_value: float
    lower_bound: float
    upper_bound: float

class ScenarioSchema(BaseModel):
    scenario_type: str
    scenario_series: List[Dict[str, Any]]
    business_impact_score: Optional[float]

class ForecastModelSchema(BaseModel):
    model_name: str
    is_selected: bool
    aic: Optional[float]
    rmse: Optional[float]
    predictions: List[PredictionPointSchema]
    scenarios: List[ScenarioSchema]
    
class ForecastSummaryResponse(BaseModel):
    column_name: str
    selected_model: str
    rmse: Optional[float]
    aic: Optional[float]
