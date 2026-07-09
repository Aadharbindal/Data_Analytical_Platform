from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.ai_gateway import TaskType, RequestStatus, ProviderStatus, CircuitState

class ChatMessage(BaseModel):
    role: str = Field(..., description="user, assistant, system")
    content: str

class GenerateRequest(BaseModel):
    messages: List[ChatMessage]
    task_type: TaskType = Field(default=TaskType.CHAT)
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Routing Hints
    max_cost_usd: Optional[float] = None
    max_latency_ms: Optional[float] = None
    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None
    required_capabilities: Optional[List[str]] = None
    
    # Model Params
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    json_mode: Optional[bool] = False

class ProviderUsed(BaseModel):
    provider_name: str
    model_name: str
    latency_ms: float

class GenerateResponse(BaseModel):
    content: str
    finish_reason: str
    model_used: str
    provider_used: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    fallback_used: bool
    fallback_chain: List[ProviderUsed] = []
    retry_count: int

class ModelResponse(BaseModel):
    id: str
    model_id: str
    display_name: str
    provider_name: str
    context_window: int
    input_cost_per_1m: float
    output_cost_per_1m: float
    is_available: bool
    avg_latency_ms: Optional[float]

class ProviderResponse(BaseModel):
    id: str
    name: str
    display_name: str
    status: ProviderStatus
    circuit_state: CircuitState

class UsageStatsResponse(BaseModel):
    workspace_id: Optional[str]
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float

class HealthResponse(BaseModel):
    provider_name: str
    model_name: Optional[str]
    is_available: bool
    p50_latency_ms: Optional[float]
    p95_latency_ms: Optional[float]
    error_rate: float
    last_checked_at: datetime
