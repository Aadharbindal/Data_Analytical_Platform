from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class CleaningRecommendationResponse(BaseModel):
    id: str
    recommended_operation: str
    target_column: Optional[str]
    recommended_parameters: Dict[str, Any]
    confidence_score: float
    reasoning: Optional[str]
    
    class Config:
        from_attributes = True

class TransformationStepRequest(BaseModel):
    operation_type: str
    target_column: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

class PipelineApplyRequest(BaseModel):
    steps: List[TransformationStepRequest]

class PreviewResponse(BaseModel):
    before_sample: List[Dict[str, Any]]
    after_sample: List[Dict[str, Any]]
    affected_columns: List[str]
    steps_simulated: int
    
class CleaningHistoryResponse(BaseModel):
    id: str
    executed_at: datetime
    execution_time_ms: Optional[int]
    affected_rows: Optional[int]
    snapshot_steps: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True
