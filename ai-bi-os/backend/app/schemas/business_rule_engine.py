from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class RuleCreateRequest(BaseModel):
    workspace_id: str
    department: Optional[str] = None
    rule_name: str
    rule_category: str
    description: str
    priority: int = 5
    severity: str = "MEDIUM"
    expression_ast: Dict[str, Any]
    action: str
    author: Optional[str] = None

class RuleValidateRequest(BaseModel):
    expression_ast: Dict[str, Any]

class RuleEvaluateRequest(BaseModel):
    workspace_id: str
    rule_ids: Optional[List[str]] = None # If none, evaluate all active rules in workspace
    input_objects: Dict[str, Any]

class RulePublishRequest(BaseModel):
    rule_id: str
    reviewer: Optional[str] = None

class RuleVersionResponse(BaseModel):
    id: str
    version: int
    expression_ast: Dict[str, Any]
    action: str
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RuleResponse(BaseModel):
    id: str
    workspace_id: str
    department: Optional[str]
    rule_name: str
    rule_category: str
    description: str
    priority: int
    severity: str
    expression_ast: Dict[str, Any]
    action: str
    status: str
    version: int
    author: Optional[str]
    reviewer: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RuleExecutionResponse(BaseModel):
    id: str
    rule_id: str
    evaluation_result: str
    triggered_action: Optional[str]
    execution_time_ms: int
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RuleListResponse(BaseModel):
    rules: List[RuleResponse]
    total: int
