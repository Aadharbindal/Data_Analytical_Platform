from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class RuleConditionSchema(BaseModel):
    ast: Dict[str, Any]
    
    class Config:
        from_attributes = True

class BusinessRuleCreate(BaseModel):
    workspace_id: str
    name: str
    description: Optional[str]
    business_domain: str
    priority: str
    severity: str
    condition: RuleConditionSchema

class BusinessRuleSchema(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: Optional[str]
    business_domain: str
    priority: str
    severity: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    condition: Optional[RuleConditionSchema]
    
    class Config:
        from_attributes = True

class DecisionSchema(BaseModel):
    id: str
    dataset_version_id: str
    rule_id: str
    insight_id: Optional[str]
    title: str
    description: Optional[str]
    priority: str
    severity: str
    business_domain: str
    affected_entities: Optional[List[Any]]
    confidence: Optional[float]
    generated_at: datetime
    
    class Config:
        from_attributes = True
