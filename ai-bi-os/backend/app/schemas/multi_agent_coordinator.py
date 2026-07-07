from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class RegisterAgentRequest(BaseModel):
    workspace_id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    capabilities: List[str] = []
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}

class AgentResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: Optional[str]
    version: str
    status: str
    health: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class WorkflowExecuteRequest(BaseModel):
    workspace_id: str
    request_payload: Dict[str, Any]

class WorkflowNodeSchema(BaseModel):
    id: str
    task_name: str
    status: str
    agent_id: str
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)

class WorkflowExecutionResponse(BaseModel):
    id: str
    workspace_id: str
    status: str
    unified_response: Optional[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]
    
    nodes: List[WorkflowNodeSchema] = []
    
    model_config = ConfigDict(from_attributes=True)

class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowExecutionResponse]
    total: int
