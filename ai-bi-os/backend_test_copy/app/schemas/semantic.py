from pydantic import BaseModel
from typing import List, Optional, Any

class SemanticDomainResponse(BaseModel):
    primary_domain: str
    confidence_score: float
    matched_rules: List[str]
    
    class Config:
        from_attributes = True

class BusinessEntityResponse(BaseModel):
    entity_name: str
    confidence_score: float
    
    class Config:
        from_attributes = True

class BusinessMetricResponse(BaseModel):
    metric_name: str
    confidence_score: float
    
    class Config:
        from_attributes = True

class SemanticColumnResponse(BaseModel):
    column_type: str
    business_name: str
    
    class Config:
        from_attributes = True

class BusinessGlossaryResponse(BaseModel):
    term: str
    definition: str
    
    class Config:
        from_attributes = True

class OntologyNodeResponse(BaseModel):
    node_label: str
    node_type: str
    
    class Config:
        from_attributes = True

class OntologyEdgeResponse(BaseModel):
    relation_name: str
    
    class Config:
        from_attributes = True

class SemanticRecommendationResponse(BaseModel):
    recommendation_text: str
    capability: str
    
    class Config:
        from_attributes = True
