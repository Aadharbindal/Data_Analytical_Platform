from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class QualityScoreResponse(BaseModel):
    overall_score: float
    business_readiness_score: float
    analytics_readiness_score: float
    ai_readiness_score: float
    
    class Config:
        from_attributes = True

class QualityDimensionResponse(BaseModel):
    id: str
    dimension_name: str
    score: float
    confidence: float
    explanation: Optional[str]
    
    class Config:
        from_attributes = True

class QualityViolationResponse(BaseModel):
    id: str
    schema_column_id: Optional[str]
    issue_category: str
    severity: str
    priority: str
    affected_rows_count: int
    root_cause: Optional[str]
    suggested_fix: Optional[str]
    
    class Config:
        from_attributes = True

class QualityAssessmentResponse(BaseModel):
    id: str
    dataset_version_id: str
    created_at: datetime
    
    score: Optional[QualityScoreResponse] = None
    dimensions: List[QualityDimensionResponse] = []
    
    class Config:
        from_attributes = True

class QualityReportResponse(BaseModel):
    assessment: QualityAssessmentResponse
    critical_issues: List[QualityViolationResponse]
    warnings: List[QualityViolationResponse]
