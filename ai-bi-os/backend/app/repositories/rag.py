from sqlalchemy.orm import Session
from app.models.rag import (
    KnowledgeDocument,
    KnowledgeChunk,
    RetrievalHistory,
    RetrievalMetrics,
    RetrievalAudit
)
from typing import List, Optional

class KnowledgeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_document(self, workspace_id: str, filename: str, file_type: str, dataset_id: str = None) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            workspace_id=workspace_id,
            filename=filename,
            file_type=file_type,
            dataset_id=dataset_id,
            status="INDEXING"
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc
        
    def update_document_status(self, doc_id: str, status: str):
        doc = self.db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if doc:
            doc.status = status
            self.db.commit()
            
    def create_chunk(self, document_id: str, sequence_number: int, text_content: str) -> KnowledgeChunk:
        chunk = KnowledgeChunk(
            document_id=document_id,
            sequence_number=sequence_number,
            text_content=text_content
        )
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk
        
    def get_documents_by_workspace(self, workspace_id: str) -> List[KnowledgeDocument]:
        return self.db.query(KnowledgeDocument).filter(KnowledgeDocument.workspace_id == workspace_id).all()
        
    def get_chunks_by_workspace(self, workspace_id: str) -> List[KnowledgeChunk]:
        return self.db.query(KnowledgeChunk).join(KnowledgeDocument).filter(KnowledgeDocument.workspace_id == workspace_id).all()
        
    def log_retrieval(self, workspace_id: str, query_text: str, retrieved_count: int, time_ms: int, cache_hit: bool) -> RetrievalHistory:
        history = RetrievalHistory(
            workspace_id=workspace_id,
            query_text=query_text,
            retrieved_count=retrieved_count
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        
        metrics = RetrievalMetrics(
            history_id=history.id,
            retrieval_time_ms=time_ms,
            cache_hit=cache_hit
        )
        self.db.add(metrics)
        self.db.commit()
        
        return history

    def get_history(self, workspace_id: str) -> List[RetrievalHistory]:
        return self.db.query(RetrievalHistory).filter(RetrievalHistory.workspace_id == workspace_id).order_by(RetrievalHistory.created_at.desc()).all()
        
    def search_chunks_by_keyword(self, workspace_id: str, query: str, top_k: int = 5) -> List[KnowledgeChunk]:
        # Simple keyword fallback for Module 40
        # In a real system, this would be a full-text search or vector search
        return self.db.query(KnowledgeChunk).join(KnowledgeDocument).filter(
            KnowledgeDocument.workspace_id == workspace_id,
            KnowledgeChunk.text_content.ilike(f"%{query}%")
        ).limit(top_k).all()
