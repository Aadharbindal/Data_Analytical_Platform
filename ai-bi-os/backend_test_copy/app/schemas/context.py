from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ContextRankingSchema(BaseModel):
    semantic_score: Optional[float]
    confidence_score: Optional[float]
    final_score: float
    
    class Config:
        from_attributes = True

class ContextSelectionSchema(BaseModel):
    reason: str
    selection_method: str
    
    class Config:
        from_attributes = True

class ContextItemSchema(BaseModel):
    source_type: str
    source_id: str
    content: Dict[str, Any]
    estimated_tokens: int
    
    ranking: Optional[ContextRankingSchema]
    selection: Optional[ContextSelectionSchema]
    
    class Config:
        from_attributes = True

class ContextPackageSchema(BaseModel):
    id: str
    workspace_id: str
    dataset_version_id: Optional[str]
    question: str
    inferred_intent: Optional[str]
    token_budget: int
    estimated_tokens: int
    generated_at: datetime
    
    items: List[ContextItemSchema] = []
    
    class Config:
        from_attributes = True

class ContextBuildRequest(BaseModel):
    workspace_id: str
    dataset_version_id: Optional[str]
    question: str
    token_budget: Optional[int] = 8000
