from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

class PromptSectionBase(BaseModel):
    section_name: str
    content: str
    section_priority: int = 1
    model_config = ConfigDict(from_attributes=True)

class PromptReferenceBase(BaseModel):
    source_type: str
    source_id: str
    model_config = ConfigDict(from_attributes=True)

class PromptOptimizationBase(BaseModel):
    original_size: int
    optimized_size: int
    optimization_ratio: float
    actions_taken: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(from_attributes=True)

class PromptValidationBase(BaseModel):
    is_valid: bool
    validation_type: str
    details: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class PromptPayload(BaseModel):
    system_instructions: Optional[str] = None
    business_context: Optional[str] = None
    dataset_context: Optional[str] = None
    analytics_context: Optional[str] = None
    evidence_context: Optional[str] = None
    conversation_context: Optional[str] = None
    user_request: Optional[str] = None
    constraints: Optional[str] = None
    output_format: Optional[str] = None
    safety_rules: Optional[str] = None
    validation_rules: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class PromptObjectBase(BaseModel):
    workspace_id: str
    conversation_id: Optional[str] = None
    request_id: Optional[str] = None
    
    prompt_type: str
    prompt_version: str = "1.0"
    
    prompt_priority: int = 1
    prompt_size: int = 0
    estimated_tokens: int = 0
    
    structured_prompt: PromptPayload
    validation_status: str = "PENDING"
    
    model_config = ConfigDict(from_attributes=True)

class PromptObjectCreate(PromptObjectBase):
    sections: List[PromptSectionBase] = Field(default_factory=list)
    references: List[PromptReferenceBase] = Field(default_factory=list)
    metadata_info: Dict[str, Any] = Field(default_factory=dict)
    optimizations: Optional[PromptOptimizationBase] = None
    validations: List[PromptValidationBase] = Field(default_factory=list)

class PromptObjectResponse(PromptObjectBase):
    id: str
    created_timestamp: datetime
    
    sections: List[PromptSectionBase] = Field(default_factory=list)
    references: List[PromptReferenceBase] = Field(default_factory=list)
    optimizations: List[PromptOptimizationBase] = Field(default_factory=list)
    validations: List[PromptValidationBase] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)

class PromptBuildRequest(BaseModel):
    workspace_id: str
    conversation_id: Optional[str] = None
    request_id: Optional[str] = None
    
    context_id: str
    evidence_id: str
    
    user_request: Optional[str] = None
    prompt_type: str = "AnalyticsPrompt"

class PromptValidationRequest(BaseModel):
    prompt_id: str

class PromptOptimizationRequest(BaseModel):
    prompt_id: str
