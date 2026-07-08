from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class BenchmarkRequest(BaseModel):
    workspace_id: str
    evaluation_type: str # MODEL, PROMPT, WORKFLOW
    target_module: str
    suite_id: Optional[str] = None
    model_version: Optional[str] = None
    prompt_version: Optional[str] = None

class MetricSchema(BaseModel):
    metric_name: str
    metric_value: float
    
    model_config = ConfigDict(from_attributes=True)

class EvaluationResponse(BaseModel):
    id: str
    workspace_id: str
    evaluation_type: str
    target_module: str
    model_version: Optional[str]
    prompt_version: Optional[str]
    quality_score: float
    cost_score: float
    latency_score: float
    overall_score: float
    timestamp: datetime
    
    metrics: List[MetricSchema] = []
    
    model_config = ConfigDict(from_attributes=True)

class LeaderboardResponse(BaseModel):
    id: str
    category: str
    entity_name: str
    overall_rank: int
    aggregated_score: float
    last_updated: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RegressionReportResponse(BaseModel):
    id: str
    metric_name: str
    previous_value: float
    current_value: float
    degradation_percentage: float
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class EvaluationListResponse(BaseModel):
    evaluations: List[EvaluationResponse]
    total: int
