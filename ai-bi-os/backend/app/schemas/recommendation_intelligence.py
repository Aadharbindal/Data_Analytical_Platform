from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class RecommendationReferenceSchema(BaseModel):
    reference_type: str
    reference_id: str

class RecommendationGenerateRequest(BaseModel):
    workspace_id: str
    dataset_id: Optional[str] = None
    insight_id: str
    
    business_domain: str = "General"
    recommendation_type: str = "General Action"
    
    insight_references: List[RecommendationReferenceSchema] = []
    evidence_references: List[RecommendationReferenceSchema] = []

class RecommendationRegenerateRequest(BaseModel):
    recommendation_id: str
    feedback: Optional[str] = None

class ScenarioResponse(BaseModel):
    id: str
    scenario_type: str
    description: str
    financial_impact: float
    operational_impact: Optional[str]
    strategic_impact: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)

class ActionPlanResponse(BaseModel):
    id: str
    immediate_actions: List[str]
    short_term_actions: List[str]
    medium_term_actions: List[str]
    long_term_actions: List[str]
    dependencies: Optional[List[str]]
    required_resources: Optional[List[str]]
    success_metrics: Optional[List[str]]
    kpis_to_monitor: Optional[List[str]]
    
    model_config = ConfigDict(from_attributes=True)

class RecommendationResponse(BaseModel):
    id: str
    workspace_id: str
    insight_id: str
    business_domain: str
    recommendation_type: str
    title: str
    executive_summary: str
    detailed_recommendation: str
    expected_benefit: str
    estimated_risk: str
    estimated_cost: str
    implementation_difficulty: str
    confidence_score: float
    priority: int
    status: str
    generated_at: datetime
    
    action_plan: Optional[ActionPlanResponse]
    scenarios: List[ScenarioResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class RecommendationListResponse(BaseModel):
    recommendations: List[RecommendationResponse]
    total: int

class RecommendationSummaryResponse(BaseModel):
    total_recommendations: int
    avg_confidence: float
    avg_roi: float
