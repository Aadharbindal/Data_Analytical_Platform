from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

class EvidenceScoreBase(BaseModel):
    quality_score: Optional[float] = None
    freshness_score: Optional[float] = None
    reliability_score: Optional[float] = None
    completeness_score: Optional[float] = None
    consistency_score: Optional[float] = None
    business_relevance: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class EvidenceReferenceBase(BaseModel):
    source_type: str
    source_id: str
    model_config = ConfigDict(from_attributes=True)

class EvidenceConflictBase(BaseModel):
    conflict_type: str
    conflict_description: str
    conflicting_object_id: Optional[str] = None
    resolved: bool = False
    model_config = ConfigDict(from_attributes=True)

class EvidencePayload(BaseModel):
    supporting_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    supporting_statistics: List[Dict[str, Any]] = Field(default_factory=list)
    supporting_objects: List[Dict[str, Any]] = Field(default_factory=list)
    supporting_charts_metadata: List[Dict[str, Any]] = Field(default_factory=list)
    supporting_tables_metadata: List[Dict[str, Any]] = Field(default_factory=list)
    analytical_method_used: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

class EvidenceObjectBase(BaseModel):
    workspace_id: str
    dataset_id: Optional[str] = None
    dataset_version: Optional[str] = None
    context_id: str
    
    evidence_type: str
    evidence_category: str
    evidence_priority: int = 0
    
    evidence_confidence: float = 0.0
    business_confidence: float = 0.0
    validation_status: str = "PENDING"
    
    payload: EvidencePayload
    
    model_config = ConfigDict(from_attributes=True)

class EvidenceObjectCreate(EvidenceObjectBase):
    references: List[EvidenceReferenceBase] = Field(default_factory=list)
    scores: Optional[EvidenceScoreBase] = None
    metadata_info: Dict[str, Any] = Field(default_factory=dict)

class EvidenceObjectResponse(EvidenceObjectBase):
    id: str
    created_timestamp: datetime
    
    references: List[EvidenceReferenceBase] = Field(default_factory=list)
    scores: List[EvidenceScoreBase] = Field(default_factory=list)
    conflicts: List[EvidenceConflictBase] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)

class EvidenceBuildRequest(BaseModel):
    workspace_id: str
    context_id: str
    dataset_id: Optional[str] = None
    dataset_version: Optional[str] = None

class EvidenceValidationRequest(BaseModel):
    evidence_id: str
