from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SchemaColumnResponse(BaseModel):
    id: str
    position: int
    original_header: str
    normalized_header: str
    detected_data_type: str
    inferred_semantic_type: Optional[str]
    business_meaning: Optional[str]
    classification: Optional[str]
    is_nullable: bool
    is_unique: bool
    is_primary_key_candidate: bool
    is_foreign_key_candidate: bool
    
    class Config:
        from_attributes = True

class SchemaQualityResponse(BaseModel):
    completeness_score: float
    naming_quality_score: float
    consistency_score: float
    normalization_score: float
    relationship_score: float
    overall_quality_score: float
    
    class Config:
        from_attributes = True

class SchemaFingerprintResponse(BaseModel):
    dataset_signature: str
    schema_hash: str
    column_hash: str
    structure_hash: str
    
    class Config:
        from_attributes = True
        
class SchemaRelationshipResponse(BaseModel):
    id: str
    source_column_id: str
    target_entity_name: str
    target_column_name: str
    confidence_score: float
    
    class Config:
        from_attributes = True

class DatasetSchemaResponse(BaseModel):
    id: str
    dataset_version_id: str
    created_at: datetime
    updated_at: datetime
    
    columns: List[SchemaColumnResponse] = []
    quality: Optional[SchemaQualityResponse] = None
    fingerprint: Optional[SchemaFingerprintResponse] = None
    relationships: List[SchemaRelationshipResponse] = []
    
    class Config:
        from_attributes = True
