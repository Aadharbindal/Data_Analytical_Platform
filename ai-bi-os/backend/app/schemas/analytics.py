from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class InsightObjectSchema(BaseModel):
    id: str
    title: str
    description: str
    metric: str
    evidence_data: Dict[str, Any]
    calculation_method: str
    confidence: Optional[float]
    severity: Optional[str]
    affected_dimensions: Optional[List[str]]
    generated_at: datetime
    
    class Config:
        from_attributes = True

class BusinessMetricSchema(BaseModel):
    metric_name: str
    value: float
    aggregation_level: str
    dimension: Optional[str]
    dimension_value: Optional[str]
    
    class Config:
        from_attributes = True

class AnalyticsSummaryResponse(BaseModel):
    run_id: str
    status: str
    execution_time_ms: float
    metrics_generated: int
    started_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True
