from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

# Context Section Structures
class BusinessContext(BaseModel):
    organization: Optional[str] = None
    workspace: Optional[str] = None
    business_domain: Optional[str] = None
    industry: Optional[str] = None
    currency: Optional[str] = None
    region: Optional[str] = None
    timezone: Optional[str] = None
    business_calendar: Optional[str] = None
    fiscal_calendar: Optional[str] = None

class AnalyticsContext(BaseModel):
    kpis: List[Dict[str, Any]] = Field(default_factory=list)
    business_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    eda_summary: Optional[Dict[str, Any]] = None
    data_quality: Optional[Dict[str, Any]] = None
    correlation_summary: Optional[Dict[str, Any]] = None
    regression_summary: Optional[Dict[str, Any]] = None
    trend_summary: Optional[Dict[str, Any]] = None
    forecast_summary: Optional[Dict[str, Any]] = None
    outlier_summary: Optional[Dict[str, Any]] = None
    confidence_scores: Dict[str, float] = Field(default_factory=dict)

class DatasetContext(BaseModel):
    dataset_name: Optional[str] = None
    schema_info: Optional[Dict[str, Any]] = None
    columns: List[Dict[str, Any]] = Field(default_factory=list)
    primary_metrics: List[str] = Field(default_factory=list)
    dimensions: List[str] = Field(default_factory=list)
    time_columns: List[str] = Field(default_factory=list)
    business_entities: List[str] = Field(default_factory=list)
    semantic_metadata: Optional[Dict[str, Any]] = None

class UserContext(BaseModel):
    role: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    workspace: Optional[str] = None
    language: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    feature_flags: Optional[Dict[str, bool]] = None

class QuestionContext(BaseModel):
    user_intent: Optional[str] = None
    requested_metrics: List[str] = Field(default_factory=list)
    requested_dimensions: List[str] = Field(default_factory=list)
    requested_time_window: Optional[str] = None
    requested_granularity: Optional[str] = None
    requested_business_domain: Optional[str] = None

class ContextPayload(BaseModel):
    business_context: BusinessContext = Field(default_factory=BusinessContext)
    analytics_context: AnalyticsContext = Field(default_factory=AnalyticsContext)
    dataset_context: DatasetContext = Field(default_factory=DatasetContext)
    user_context: UserContext = Field(default_factory=UserContext)
    question_context: QuestionContext = Field(default_factory=QuestionContext)

# API Request/Response Structures
class ContextBuildRequest(BaseModel):
    workspace_id: str
    dataset_id: Optional[str] = None
    conversation_id: Optional[str] = None
    request_id: Optional[str] = None
    question: Optional[str] = None
    business_domain: Optional[str] = None

class ContextObjectBase(BaseModel):
    workspace_id: str
    dataset_id: Optional[str] = None
    dataset_version: Optional[str] = None
    conversation_id: Optional[str] = None
    request_id: Optional[str] = None
    context_purpose: Optional[str] = None
    business_domain: Optional[str] = None
    context_payload: ContextPayload
    model_config = ConfigDict(from_attributes=True)

class ContextObjectCreate(ContextObjectBase):
    pass

class ContextReferenceResponse(BaseModel):
    analytics_object_id: str
    relevance_score: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class ContextObjectResponse(ContextObjectBase):
    id: str
    generated_timestamp: datetime
    references: List[ContextReferenceResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

class ContextValidationRequest(BaseModel):
    context_id: str

class ContextValidationResponse(BaseModel):
    is_valid: bool
    missing_objects: List[str] = Field(default_factory=list)
    stale_objects: List[str] = Field(default_factory=list)
    low_confidence_objects: List[str] = Field(default_factory=list)
    broken_dependencies: List[str] = Field(default_factory=list)
    version_mismatches: List[str] = Field(default_factory=list)
