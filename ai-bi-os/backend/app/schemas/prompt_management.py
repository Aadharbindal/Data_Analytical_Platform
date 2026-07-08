from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

class PromptTemplateCreate(BaseModel):
    workspace_id: str
    name: str
    description: Optional[str] = None
    prompt_type: str
    template_structure: Dict[str, Any]
    variables: List[str]

class PromptTemplateResponse(PromptTemplateCreate):
    id: str
    registry_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PromptVersionCreate(BaseModel):
    template_id: str
    parent_version_id: Optional[str] = None
    is_major: bool = False
    content: Dict[str, Any]
    estimated_tokens: int = 0
    author_id: str

class PromptLifecycleResponse(BaseModel):
    status: str
    published_at: Optional[datetime] = None
    rollback_reference: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class PromptVersionResponse(BaseModel):
    id: str
    template_id: str
    parent_version_id: Optional[str] = None
    version_string: str
    content: Dict[str, Any]
    estimated_tokens: int
    author_id: str
    created_at: datetime
    lifecycle: Optional[PromptLifecycleResponse] = None
    model_config = ConfigDict(from_attributes=True)

class PromptReviewRequest(BaseModel):
    version_id: str
    reviewer_id: str
    comments: Optional[str] = None

class PromptApproveRequest(BaseModel):
    version_id: str
    approver_id: str

class PromptPublishRequest(BaseModel):
    version_id: str
    actor_id: str

class PromptRollbackRequest(BaseModel):
    version_id: str
    actor_id: str
    rollback_to_version_id: str

class PromptDiffResponse(BaseModel):
    version_id: str
    added_sections: List[str]
    removed_sections: List[str]
    modified_sections: List[str]
    token_delta: int
    model_config = ConfigDict(from_attributes=True)

class PromptHistoryResponse(BaseModel):
    id: str
    actor_id: str
    action: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
