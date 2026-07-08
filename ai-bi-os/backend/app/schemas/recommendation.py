from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ActionStepSchema(BaseModel):
    order_index: int
    title: str
    description: Optional[str]
    estimated_duration: Optional[str]
    difficulty: Optional[str]
    
    class Config:
        from_attributes = True

class ActionPlanSchema(BaseModel):
    title: str
    business_objective: Optional[str]
    expected_outcome: Optional[str]
    steps: List[ActionStepSchema] = []
    
    class Config:
        from_attributes = True

class ImpactEstimationSchema(BaseModel):
    revenue_increase: Optional[float]
    cost_reduction: Optional[float]
    risk_reduction: Optional[float]
    
    class Config:
        from_attributes = True

class RecommendationScoreSchema(BaseModel):
    final_score: float
    confidence_score: Optional[float]
    
    class Config:
        from_attributes = True

class RecommendationSchema(BaseModel):
    id: str
    dataset_version_id: str
    decision_id: str
    title: str
    description: Optional[str]
    business_domain: str
    category: str
    priority: str
    severity: str
    roi_estimate: Optional[float]
    status: str
    generated_at: datetime
    
    score: Optional[RecommendationScoreSchema]
    action_plan: Optional[ActionPlanSchema]
    impact_estimation: Optional[ImpactEstimationSchema]
    
    class Config:
        from_attributes = True
