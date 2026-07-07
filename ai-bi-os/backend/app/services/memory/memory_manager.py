import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.memory import MemoryObject, MemoryHistory, MemoryMetrics
from app.schemas.memory import MemoryCreateRequest, MemoryUpdateRequest, MemorySearchRequest
from app.repositories.memory_repository import MemoryRepository

class MemoryCache:
    """In-memory cache acting as a fallback if Redis is not configured."""
    _cache = {}
    
    @classmethod
    def get(cls, key: str):
        return cls._cache.get(key)
        
    @classmethod
    def set(cls, key: str, value: Any):
        cls._cache[key] = value
        
    @classmethod
    def delete(cls, key: str):
        if key in cls._cache:
            del cls._cache[key]


class MemoryPolicyEngine:
    """Enforces workspace isolation, limits, and retention."""
    def __init__(self, db: Session):
        self.db = db
        
    def validate_creation(self, request: MemoryCreateRequest):
        # Enforce workspace constraints, memory size limits etc.
        # This is a stub for the validation logic.
        if not request.workspace_id:
            raise ValueError("Workspace ID is required for memory creation.")

class MemoryWriter:
    """Handles creating, updating, and archiving memories."""
    def __init__(self, repository: MemoryRepository, policy_engine: MemoryPolicyEngine):
        self.repository = repository
        self.policy_engine = policy_engine

    def write(self, request: MemoryCreateRequest) -> MemoryObject:
        start_time = time.time()
        self.policy_engine.validate_creation(request)
        
        memory = MemoryObject(
            workspace_id=request.workspace_id,
            memory_type=request.memory_type,
            summary=request.summary,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            dataset_id=request.dataset_id,
            context_id=request.context_id,
            importance_score=request.importance_score,
            confidence=request.confidence,
            evidence_references=request.evidence_references,
            tags=request.tags,
            expires_at=request.expires_at
        )
        
        created = self.repository.create_memory(memory)
        
        # Log History
        history = MemoryHistory(
            memory_id=created.id,
            action="CREATED"
        )
        self.repository.add_history(history)
        
        # Log Metrics
        latency = int((time.time() - start_time) * 1000)
        self.repository.log_metrics(MemoryMetrics(operation="WRITE", latency_ms=latency, item_count=1))
        
        # Cache
        MemoryCache.set(created.id, created)
        
        return created

    def archive(self, memory_id: str):
        memory = self.repository.get_memory(memory_id)
        if memory and not memory.is_archived:
            memory.is_archived = True
            self.repository.update_memory(memory)
            self.repository.add_history(MemoryHistory(memory_id=memory.id, action="ARCHIVED"))
            MemoryCache.delete(memory_id)

    def restore(self, memory_id: str):
        memory = self.repository.get_memory(memory_id)
        if memory and memory.is_archived:
            memory.is_archived = False
            self.repository.update_memory(memory)
            self.repository.add_history(MemoryHistory(memory_id=memory.id, action="RESTORED"))
            MemoryCache.set(memory_id, memory)

class MemoryRetriever:
    """Handles searching and retrieving memories."""
    def __init__(self, repository: MemoryRepository):
        self.repository = repository

    def get(self, memory_id: str) -> Optional[MemoryObject]:
        start_time = time.time()
        
        # Check Cache
        cached = MemoryCache.get(memory_id)
        if cached:
            latency = int((time.time() - start_time) * 1000)
            self.repository.log_metrics(MemoryMetrics(operation="RETRIEVAL", latency_ms=latency, item_count=1, cache_hit=True))
            return cached
            
        memory = self.repository.get_memory(memory_id)
        
        latency = int((time.time() - start_time) * 1000)
        self.repository.log_metrics(MemoryMetrics(operation="RETRIEVAL", latency_ms=latency, item_count=1, cache_hit=False))
        
        if memory:
            MemoryCache.set(memory_id, memory)
            
        return memory
        
    def search(self, request: MemorySearchRequest) -> List[MemoryObject]:
        start_time = time.time()
        results = self.repository.search_memories(
            workspace_id=request.workspace_id,
            memory_type=request.memory_type,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            min_importance=request.min_importance
        )
        
        # In-memory tag filtering if DB doesn't support JSON containment easily
        if request.tags:
            filtered = []
            for r in results:
                if r.tags and any(t in r.tags for t in request.tags):
                    filtered.append(r)
            results = filtered
            
        latency = int((time.time() - start_time) * 1000)
        self.repository.log_metrics(MemoryMetrics(operation="RETRIEVAL", latency_ms=latency, item_count=len(results), cache_hit=False))
        
        return results

class MemoryManager:
    """High level orchestrator for memory operations."""
    def __init__(self, db: Session):
        self.db = db
        self.repository = MemoryRepository(db)
        self.policy_engine = MemoryPolicyEngine(db)
        self.writer = MemoryWriter(self.repository, self.policy_engine)
        self.retriever = MemoryRetriever(self.repository)
