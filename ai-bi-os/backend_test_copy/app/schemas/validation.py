from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ValidationRuleSchema(BaseModel):
    metric_name: str
    operator: str
    threshold_value: float
    is_critical: bool

class ValidateObjectRequest(BaseModel):
    target_object_id: str
    target_object_type: str
    metadata: Dict[str, Any]
    rules: List[ValidationRuleSchema]

class ValidationResponse(BaseModel):
    validation_id: str
    status: str
    confidence_score: float
    reliability_score: float
    errors: List[str]
    warnings: List[str]
    execution_time_ms: float

class ConfidenceScoreResponse(BaseModel):
    overall_confidence: float
    statistical_confidence: Optional[float]
    data_confidence: Optional[float]
    model_confidence: Optional[float]
    business_confidence: Optional[float]
    prediction_confidence: Optional[float]
    confidence_level: str
    confidence_grade: str

class ReliabilityScoreResponse(BaseModel):
    reliability_score: float
    trust_score: float
    business_readiness_score: float
    production_readiness_score: float
    explainability_score: float
