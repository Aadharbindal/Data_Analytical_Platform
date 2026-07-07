from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Text, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class EmbeddingModel(Base):
    """Stores configuration for a given embedding model."""
    __tablename__ = "vector_embedding_models"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    provider = Column(String, nullable=False) # OpenAI, Voyage AI, Cohere, etc.
    dimensions = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    versions = relationship("EmbeddingVersion", back_populates="model", cascade="all, delete-orphan")
    embeddings = relationship("EmbeddingObject", back_populates="model")

class EmbeddingVersion(Base):
    """Tracks versions of embedding models."""
    __tablename__ = "vector_embedding_versions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    model_id = Column(String, ForeignKey("vector_embedding_models.id", ondelete="CASCADE"))
    version_string = Column(String, nullable=False)
    is_deprecated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    model = relationship("EmbeddingModel", back_populates="versions")

class EmbeddingObject(Base):
    """The core entity storing the vector embedding."""
    __tablename__ = "vector_embedding_objects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    model_id = Column(String, ForeignKey("vector_embedding_models.id", ondelete="SET NULL"), nullable=True)
    
    workspace_id = Column(String, nullable=False, index=True)
    dataset_id = Column(String, nullable=True, index=True)
    document_id = Column(String, nullable=True, index=True)
    chunk_id = Column(String, nullable=True, index=True)
    
    # Using JSON for simplicity across different DBs.
    # In a pure pgvector setup, this would be a Vector type, but AI BI OS
    # requires supporting Qdrant, Pinecone, Milvus via abstraction.
    # We store the raw vector here for reference or fallback.
    vector_data = Column(JSON, nullable=True) 
    
    dimensions = Column(Integer, nullable=False)
    similarity_score = Column(Float, nullable=True) # Used if this object represents a search result
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    model = relationship("EmbeddingModel", back_populates="embeddings")
    metadata_entries = relationship("VectorMetadata", back_populates="embedding", cascade="all, delete-orphan")
    history = relationship("EmbeddingHistory", back_populates="embedding", cascade="all, delete-orphan")

class VectorIndex(Base):
    """Stores vector index configurations."""
    __tablename__ = "vector_indices"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    provider = Column(String, nullable=False) # pgvector, Qdrant, Pinecone
    index_type = Column(String, nullable=False) # HNSW, IVF, Flat
    dimensions = Column(Integer, nullable=False)
    metric = Column(String, nullable=False) # Cosine, DotProduct, Euclidean
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_reindexed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="READY") # BUILDING, READY, FAILED

class VectorMetadata(Base):
    """Flexible key-value storage for metadata attached to embeddings."""
    __tablename__ = "vector_metadata"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    embedding_id = Column(String, ForeignKey("vector_embedding_objects.id", ondelete="CASCADE"))
    
    key = Column(String, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    
    embedding = relationship("EmbeddingObject", back_populates="metadata_entries")

class EmbeddingHistory(Base):
    """Tracks history of changes to embeddings."""
    __tablename__ = "vector_embedding_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    embedding_id = Column(String, ForeignKey("vector_embedding_objects.id", ondelete="CASCADE"))
    action = Column(String, nullable=False) # CREATED, RE_EMBEDDED, DELETED
    previous_model_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    embedding = relationship("EmbeddingObject", back_populates="history")

class EmbeddingAudit(Base):
    """Tracks auditing information for embeddings."""
    __tablename__ = "vector_embedding_audit"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    operation = Column(String, nullable=False) # GENERATE, SEARCH, DELETE
    user_id = Column(String, nullable=True)
    status = Column(String, nullable=False) # SUCCESS, DENIED, FAILED
    timestamp = Column(DateTime, default=datetime.utcnow)

class EmbeddingMetrics(Base):
    """Tracks metrics like generation time, throughput."""
    __tablename__ = "vector_embedding_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    model_id = Column(String, nullable=True)
    operation = Column(String, nullable=False) # GENERATION, SEARCH
    latency_ms = Column(Integer, nullable=False)
    vector_count = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
