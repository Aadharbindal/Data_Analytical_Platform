from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class EmbeddingModelBase(BaseModel):
    name: str
    provider: str
    dimensions: int
    description: Optional[str] = None
    is_active: bool = True

class EmbeddingModelCreate(EmbeddingModelBase):
    pass

class EmbeddingModelResponse(EmbeddingModelBase):
    id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class EmbeddingGenerateRequest(BaseModel):
    workspace_id: str
    texts: List[str]
    model_name: Optional[str] = None
    dataset_id: Optional[str] = None
    document_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class EmbeddingObjectResponse(BaseModel):
    id: str
    workspace_id: str
    model_id: Optional[str]
    dimensions: int
    vector_data: Optional[List[float]] = None
    similarity_score: Optional[float] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class EmbeddingGenerateResponse(BaseModel):
    status: str
    embeddings: List[EmbeddingObjectResponse]
    metrics: Dict[str, Any]

class VectorSearchRequest(BaseModel):
    workspace_id: str
    query_text: str
    top_k: int = 10
    threshold: float = 0.7
    dataset_id: Optional[str] = None
    model_name: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

class VectorSearchResponse(BaseModel):
    query: str
    results: List[EmbeddingObjectResponse]
    latency_ms: int

class ReindexRequest(BaseModel):
    workspace_id: str
    index_name: str
    provider: str

class ReindexResponse(BaseModel):
    status: str
    message: str

class StatisticsResponse(BaseModel):
    total_vectors: int
    total_models: int
    active_indices: int
    avg_latency_ms: float
