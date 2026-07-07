from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

class ExecutionRequest(BaseModel):
    workspace_id: str
    conversation_id: Optional[str] = None
    user_request: str
    workflow_id: Optional[str] = None

class IntentClassification(BaseModel):
    intent: str
    confidence: float

class ExecutionStepSchema(BaseModel):
    step_name: str
    step_order: int
    status: str
    result: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ExecutionPlanPayload(BaseModel):
    required_context: Optional[Dict[str, Any]] = None
    required_evidence: Optional[Dict[str, Any]] = None
    required_prompt: Optional[Dict[str, Any]] = None
    required_tools: Optional[List[str]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    output_format: Optional[str] = None
    steps: List[ExecutionStepSchema] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

class ExecutionMetricsPayload(BaseModel):
    latency_ms: Optional[int] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    retries_count: int = 0
    model_config = ConfigDict(from_attributes=True)

class ExecutionResponse(BaseModel):
    id: str
    workspace_id: str
    conversation_id: Optional[str] = None
    
    user_request: str
    detected_intent: Optional[str] = None
    
    selected_agent: Optional[str] = None
    selected_model: Optional[str] = None
    
    status: str
    
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    plan: Optional[ExecutionPlanPayload] = None
    metrics: Optional[ExecutionMetricsPayload] = None
    model_config = ConfigDict(from_attributes=True)

class WorkflowTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    steps: Dict[str, Any]
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class ModelResolution(BaseModel):
    provider: str
    model_name: str
    context_window: int
    capabilities: List[str]
