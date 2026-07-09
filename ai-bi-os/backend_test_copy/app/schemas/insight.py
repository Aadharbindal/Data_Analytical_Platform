from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class InsightScoreSchema(BaseModel):
    confidence: float
    business_impact: float
    urgency: float
    novelty: float
    
    class Config:
        from_attributes = True

class InsightRankingSchema(BaseModel):
    final_score: float
    rank_position: Optional[int]
    
    class Config:
        from_attributes = True

class InsightEvidenceSchema(BaseModel):
    evidence_type: str
    reference_id: Optional[str]
    data: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class InsightSchema(BaseModel):
    id: str
    dataset_version_id: str
    title: str
    category: str
    insight_type: str
    metric: str
    severity: Optional[str]
    status: str
    generated_at: datetime
    
    score: Optional[InsightScoreSchema]
    ranking: Optional[InsightRankingSchema]
    evidence: List[InsightEvidenceSchema] = []
    
    class Config:
        from_attributes = True
