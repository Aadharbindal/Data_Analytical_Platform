from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid

class ObjectStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DEPRECATED = "DEPRECATED"
    FAILED = "FAILED"
    PENDING = "PENDING"

class ValidationStatus(str, Enum):
    VALIDATED = "VALIDATED"
    INVALID = "INVALID"
    PENDING = "PENDING"
    WARNING = "WARNING"

class ObjectDependencyBase(BaseModel):
    target_object_id: str
    dependency_type: str = "uses"

class ObjectTagBase(BaseModel):
    tag_name: str
    model_config = ConfigDict(from_attributes=True)

class AnalyticsObjectBase(BaseModel):
    object_type: str = Field(..., description="e.g., KPI, EDA, Correlation, Trend")
    workspace_id: str
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    pipeline_run_id: Optional[str] = None
    
    engine_name: str
    engine_version: str
    created_by: str
    
    confidence_score: Optional[float] = None
    quality_score: Optional[float] = None
    business_domain: Optional[str] = None
    
    payload: Dict[str, Any] = Field(default_factory=dict, description="JSON payload of the analytics object")
    
    model_config = ConfigDict(from_attributes=True)

class AnalyticsObjectCreate(AnalyticsObjectBase):
    tags: List[str] = Field(default_factory=list)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[ObjectDependencyBase] = Field(default_factory=list)
    parent_ids: List[str] = Field(default_factory=list)

class AnalyticsObjectUpdate(BaseModel):
    status: Optional[ObjectStatus] = None
    validation_status: Optional[ValidationStatus] = None
    confidence_score: Optional[float] = None
    quality_score: Optional[float] = None
    tags: Optional[List[str]] = None
    payload: Optional[Dict[str, Any]] = None

class ObjectVersionResponse(BaseModel):
    id: str
    object_id: str
    major_version: int
    minor_version: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AnalyticsObjectResponse(AnalyticsObjectBase):
    id: str
    status: ObjectStatus
    validation_status: ValidationStatus
    created_at: datetime
    updated_at: datetime
    
    # Optional nested details depending on the query
    tags: Optional[List[ObjectTagBase]] = None
    versions: Optional[List[ObjectVersionResponse]] = None
    
    model_config = ConfigDict(from_attributes=True)

class ObjectSearchRequest(BaseModel):
    workspace_id: Optional[str] = None
    dataset_id: Optional[str] = None
    object_type: Optional[str] = None
    engine_name: Optional[str] = None
    status: Optional[ObjectStatus] = None
    business_domain: Optional[str] = None
    tags: Optional[List[str]] = None
    min_confidence: Optional[float] = None
    min_quality: Optional[float] = None
    limit: int = Field(default=100, le=1000)
    offset: int = 0

class LineageNode(BaseModel):
    object_id: str
    object_type: str
    status: str

class LineageResponse(BaseModel):
    object_id: str
    parents: List[LineageNode]
    children: List[LineageNode]
    dependencies: List[LineageNode]
    dependents: List[LineageNode]
