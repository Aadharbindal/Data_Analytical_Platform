from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

class ToolPermissionSchema(BaseModel):
    role_required: str
    clearance_level: int = 1

class ToolParameterSchema(BaseModel):
    parameter_name: str
    validation_rules: Dict[str, Any]

class ToolRegistrationRequest(BaseModel):
    workspace_id: str
    tool_id_string: str
    name: str
    description: Optional[str] = None
    category: str
    version: str = "1.0.0"
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    timeout_ms: int = 30000
    retry_policy: Optional[Dict[str, Any]] = None
    permissions: List[ToolPermissionSchema] = Field(default_factory=list)
    parameters: List[ToolParameterSchema] = Field(default_factory=list)

class ToolResponse(BaseModel):
    id: str
    registry_id: str
    tool_id_string: str
    name: str
    description: Optional[str] = None
    category: str
    version: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ToolExecutionRequest(BaseModel):
    tool_id_string: str
    workflow_id: Optional[str] = None
    input_parameters: Dict[str, Any]
    actor_id: str

class ToolExecutionResponse(BaseModel):
    execution_id: str
    tool_id: str
    status: str
    output: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    latency_ms: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ToolValidationRequest(BaseModel):
    tool_id_string: str
    input_parameters: Dict[str, Any]
    actor_id: str
