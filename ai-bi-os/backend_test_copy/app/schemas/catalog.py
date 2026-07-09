from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class SearchResultResponse(BaseModel):
    dataset_id: str
    dataset_name: str
    relevance_score: float

class CatalogScoreResponse(BaseModel):
    popularity_score: float
    freshness_score: float
    quality_score: float
    trust_score: float
    ai_readiness_score: float
    
    class Config:
        from_attributes = True

class DatasetDocumentationResponse(BaseModel):
    business_summary: str
    technical_summary: str
    recommended_kpis: List[str]
    
    class Config:
        from_attributes = True

class CatalogRecommendationResponse(BaseModel):
    recommendation_type: str
    target_dataset_id: Optional[str]
    reasoning: str
    
    class Config:
        from_attributes = True

class CatalogOverviewResponse(BaseModel):
    dataset_id: str
    last_indexed_at: Any
    score: Optional[CatalogScoreResponse]
    documentation: Optional[DatasetDocumentationResponse]
    
    class Config:
        from_attributes = True

class CatalogListResponse(BaseModel):
    id: str
    name: str
    business_domain: Optional[str]
    description: Optional[str]
    column_count: int
    last_updated: Optional[datetime]
    owner: Optional[str]
    tags: List[str]

    class Config:
        from_attributes = True
