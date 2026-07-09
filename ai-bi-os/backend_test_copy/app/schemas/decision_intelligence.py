from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class DecisionReferenceSchema(BaseModel):
    reference_type: str
    reference_id: str

class DecisionGenerateRequest(BaseModel):
    workspace_id: str
    dataset_id: Optional[str] = None
    recommendation_ids: List[str]
    decision_type: str = "Strategic Decision"
    business_objective: str = "Maximize ROI"

class DecisionOptimizeRequest(BaseModel):
    decision_id: str
    optimization_goal: str # e.g. "Maximize ROI", "Minimize Risk"
    constraints: Optional[Dict[str, Any]] = None

class ScenarioResponse(BaseModel):
    id: str
    scenario_type: str
    description: str
    financial_projection: float
    operational_projection: Optional[str]
    strategic_projection: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)

class ComparisonResponse(BaseModel):
    id: str
    strategy_name: str
    description: str
    estimated_roi: float
    risk_level: str
    
    model_config = ConfigDict(from_attributes=True)

class PolicyResponse(BaseModel):
    id: str
    policy_name: str
    constraint_type: str
    constraint_value: str
    is_satisfied: bool
    
    model_config = ConfigDict(from_attributes=True)

class DecisionResponse(BaseModel):
    id: str
    workspace_id: str
    decision_type: str
    business_objective: str
    decision_summary: str
    selected_strategy: str
    expected_roi: float
    expected_revenue_impact: float
    expected_cost_impact: float
    expected_risk: str
    confidence_score: float
    business_priority: int
    approval_status: str
    generated_at: datetime
    
    scenarios: List[ScenarioResponse] = []
    comparisons: List[ComparisonResponse] = []
    policies: List[PolicyResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class DecisionListResponse(BaseModel):
    decisions: List[DecisionResponse]
    total: int
