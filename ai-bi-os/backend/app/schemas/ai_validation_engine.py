from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class ValidationRequest(BaseModel):
    workspace_id: str
    object_id: str
    object_type: str # INSIGHT, RECOMMENDATION, DECISION, SQL_RESULT, CHAT_RESPONSE
    payload: Dict[str, Any] # The actual AI output to be validated

class RevalidationRequest(BaseModel):
    validation_id: str

class ValidationResultSchema(BaseModel):
    id: str
    validator_name: str
    status: str
    message: Optional[str]
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ValidationResponse(BaseModel):
    id: str
    workspace_id: str
    object_id: str
    object_type: str
    validation_status: str
    confidence_score: float
    evidence_score: float
    policy_score: float
    warnings: Optional[List[str]]
    errors: Optional[List[str]]
    created_at: datetime
    approved_at: Optional[datetime]
    
    results: List[ValidationResultSchema] = []
    
    model_config = ConfigDict(from_attributes=True)

class ValidationListResponse(BaseModel):
    validations: List[ValidationResponse]
    total: int

class ValidationStatisticsResponse(BaseModel):
    total_validated: int
    approval_rate: float
    rejection_rate: float
    avg_confidence: float
