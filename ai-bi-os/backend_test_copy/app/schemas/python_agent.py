from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

class WorkflowStepSchema(BaseModel):
    step_id: str
    operation: str # e.g., "DROP_NULLS", "FIT_KMEANS"
    parameters: Dict[str, Any]

class WorkflowDefinitionSchema(BaseModel):
    intent: str
    steps: List[WorkflowStepSchema]
    dataset_id: str

class PythonExecutionRequest(BaseModel):
    workspace_id: str
    workflow_definition: WorkflowDefinitionSchema
    context_data: Optional[Dict[str, Any]] = None

class PythonValidationRequest(BaseModel):
    workflow_definition: WorkflowDefinitionSchema

class ExecutionArtifactResponse(BaseModel):
    artifact_id: str
    artifact_type: str
    name: str
    content_uri: str
    model_config = ConfigDict(from_attributes=True)

class PythonExecutionResponse(BaseModel):
    execution_id: str
    workflow_id: str
    status: str
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    artifacts: List[ExecutionArtifactResponse] = []
    started_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
