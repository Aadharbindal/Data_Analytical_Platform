from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class InsightReferenceSchema(BaseModel):
    reference_type: str
    reference_id: str

class InsightGenerateRequest(BaseModel):
    workspace_id: str
    dataset_id: Optional[str] = None
    conversation_id: Optional[str] = None
    insight_type: str
    business_domain: str = "General"
    evidence_references: List[InsightReferenceSchema]
    context_references: List[InsightReferenceSchema] = []
    analytics_references: List[InsightReferenceSchema] = []

class InsightRegenerateRequest(BaseModel):
    insight_id: str
    feedback: Optional[str] = None

class InsightResponse(BaseModel):
    id: str
    workspace_id: str
    insight_type: str
    business_domain: str
    headline: str
    detailed_narrative: str
    confidence_score: float
    business_impact_score: float
    priority: int
    severity: str
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class InsightListResponse(BaseModel):
    insights: List[InsightResponse]
    total: int

class InsightSummaryResponse(BaseModel):
    total_insights: int
    avg_confidence: float
    avg_business_impact: float
    top_domains: List[str]
