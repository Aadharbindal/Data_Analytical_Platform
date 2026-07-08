from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

class DocumentIndexRequest(BaseModel):
    workspace_id: str
    dataset_id: Optional[str] = None
    filename: str
    file_type: str
    content: str # For text/markdown docs
    
class DocumentResponse(BaseModel):
    id: str
    workspace_id: str
    dataset_id: Optional[str]
    filename: str
    file_type: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RetrievalRequest(BaseModel):
    workspace_id: str
    query: str
    top_k: int = 5
    metadata_filters: Optional[Dict[str, Any]] = None

class ChunkResponse(BaseModel):
    id: str
    document_id: str
    sequence_number: int
    text_content: str
    similarity_score: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class RetrievalResponse(BaseModel):
    retrieval_id: str
    workspace_id: str
    query: str
    chunks: List[ChunkResponse]
    retrieval_time_ms: int
    cache_hit: bool

class SearchRequest(BaseModel):
    workspace_id: str
    query: str
    top_k: int = 10
    
class HistoryResponse(BaseModel):
    id: str
    workspace_id: str
    query_text: str
    retrieved_count: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
