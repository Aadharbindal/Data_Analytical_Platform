from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Text, DateTime, Float
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class KnowledgeDocument(Base):
    """Stores document metadata (filename, path, status)."""
    __tablename__ = "rag_knowledge_documents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    dataset_id = Column(String, nullable=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="INDEXING") # INDEXING, INDEXED, FAILED
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")
    metadata_entries = relationship("KnowledgeMetadata", back_populates="document", cascade="all, delete-orphan")

class KnowledgeChunk(Base):
    """Stores chunks derived from documents."""
    __tablename__ = "rag_knowledge_chunks"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("rag_knowledge_documents.id", ondelete="CASCADE"))
    sequence_number = Column(Integer, nullable=False)
    
    text_content = Column(Text, nullable=False)
    # Vector embeddings omitted for Module 40. Will be added in Module 41.
    
    document = relationship("KnowledgeDocument", back_populates="chunks")
    metadata_entries = relationship("KnowledgeMetadata", back_populates="chunk", cascade="all, delete-orphan")

class KnowledgeMetadata(Base):
    """Flexible JSON metadata for chunks or documents."""
    __tablename__ = "rag_knowledge_metadata"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("rag_knowledge_documents.id", ondelete="CASCADE"), nullable=True)
    chunk_id = Column(String, ForeignKey("rag_knowledge_chunks.id", ondelete="CASCADE"), nullable=True)
    
    key = Column(String, nullable=False)
    value = Column(JSON, nullable=False)
    
    document = relationship("KnowledgeDocument", back_populates="metadata_entries")
    chunk = relationship("KnowledgeChunk", back_populates="metadata_entries")

class RetrievalHistory(Base):
    """Logs historical RAG queries."""
    __tablename__ = "rag_retrieval_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    
    retrieved_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    metrics = relationship("RetrievalMetrics", uselist=False, back_populates="history", cascade="all, delete-orphan")

class RetrievalMetrics(Base):
    """Tracks performance (latency, hit rates)."""
    __tablename__ = "rag_retrieval_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    history_id = Column(String, ForeignKey("rag_retrieval_history.id", ondelete="CASCADE"), unique=True)
    
    retrieval_time_ms = Column(Integer, nullable=False)
    cache_hit = Column(Boolean, nullable=False, default=False)
    
    history = relationship("RetrievalHistory", back_populates="metrics")

class RetrievalCache(Base):
    """Caches retrieval results for identical queries."""
    __tablename__ = "rag_retrieval_cache"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    query_hash = Column(String, nullable=False, unique=True)
    
    cached_result = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False)

class RetrievalAudit(Base):
    """Logs access and RAG operations for RBAC compliance."""
    __tablename__ = "rag_retrieval_audit"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    operation = Column(String, nullable=False) # INDEX, RETRIEVE, SEARCH
    status = Column(String, nullable=False) # ALLOWED, DENIED
    
    timestamp = Column(DateTime, default=datetime.utcnow)
