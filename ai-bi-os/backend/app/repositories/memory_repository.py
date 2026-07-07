from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from app.models.memory import MemoryObject, MemoryHistory, MemoryMetrics

class MemoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_memory(self, memory: MemoryObject) -> MemoryObject:
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory
        
    def get_memory(self, memory_id: str) -> Optional[MemoryObject]:
        return self.db.query(MemoryObject).filter(MemoryObject.id == memory_id).first()
        
    def update_memory(self, memory: MemoryObject) -> MemoryObject:
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def delete_memory(self, memory_id: str):
        memory = self.get_memory(memory_id)
        if memory:
            self.db.delete(memory)
            self.db.commit()
            
    def search_memories(self, 
                        workspace_id: str, 
                        memory_type: Optional[str] = None,
                        user_id: Optional[str] = None,
                        conversation_id: Optional[str] = None,
                        min_importance: Optional[float] = None) -> List[MemoryObject]:
        query = self.db.query(MemoryObject).filter(
            MemoryObject.workspace_id == workspace_id,
            MemoryObject.is_archived == False
        )
        
        if memory_type:
            query = query.filter(MemoryObject.memory_type == memory_type)
        if user_id:
            query = query.filter(MemoryObject.user_id == user_id)
        if conversation_id:
            query = query.filter(MemoryObject.conversation_id == conversation_id)
        if min_importance is not None:
            query = query.filter(MemoryObject.importance_score >= min_importance)
            
        # For a real implementation, tags and full-text search would be added here
        
        return query.order_by(MemoryObject.created_at.desc()).all()

    def add_history(self, history: MemoryHistory):
        self.db.add(history)
        self.db.commit()

    def get_history(self, memory_id: str) -> List[MemoryHistory]:
        return self.db.query(MemoryHistory).filter(MemoryHistory.memory_id == memory_id).order_by(MemoryHistory.timestamp.desc()).all()

    def log_metrics(self, metrics: MemoryMetrics):
        self.db.add(metrics)
        self.db.commit()

    def get_statistics(self) -> Dict[str, Any]:
        total = self.db.query(func.count(MemoryObject.id)).scalar() or 0
        archived = self.db.query(func.count(MemoryObject.id)).filter(MemoryObject.is_archived == True).scalar() or 0
        active = total - archived
        avg_retrieval = self.db.query(func.avg(MemoryMetrics.latency_ms)).filter(MemoryMetrics.operation == "RETRIEVAL").scalar() or 0.0
        
        return {
            "total_memories": total,
            "active_memories": active,
            "archived_memories": archived,
            "avg_retrieval_ms": float(avg_retrieval)
        }
