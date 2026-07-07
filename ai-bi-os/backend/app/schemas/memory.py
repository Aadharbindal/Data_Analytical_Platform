from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class MemoryCreateRequest(BaseModel):
    workspace_id: str
    memory_type: str = "Conversation" # Conversation, Workspace, User, Dataset, Business, Insight, etc.
    summary: str
    
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    dataset_id: Optional[str] = None
    context_id: Optional[str] = None
    
    importance_score: float = 0.5
    confidence: float = 1.0
    
    evidence_references: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    expires_at: Optional[datetime] = None

class MemoryUpdateRequest(BaseModel):
    summary: Optional[str] = None
    importance_score: Optional[float] = None
    confidence: Optional[float] = None
    tags: Optional[List[str]] = None
    expires_at: Optional[datetime] = None

class MemoryResponse(BaseModel):
    id: str
    memory_type: str
    workspace_id: str
    summary: str
    importance_score: float
    recency_score: float
    confidence: float
    tags: Optional[List[str]] = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class MemorySearchRequest(BaseModel):
    workspace_id: str
    memory_type: Optional[str] = None
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    tags: Optional[List[str]] = None
    query: Optional[str] = None # For basic text matching if vector isn't used
    min_importance: Optional[float] = None

class MemoryHistoryResponse(BaseModel):
    id: str
    action: str
    previous_summary: Optional[str] = None
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class MemoryStatisticsResponse(BaseModel):
    total_memories: int
    active_memories: int
    archived_memories: int
    avg_retrieval_ms: float
