from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Text, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class MemoryObject(Base):
    """Core memory tracking entity."""
    __tablename__ = "memory_objects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    memory_type = Column(String, nullable=False, index=True) # Conversation, Workspace, User, Dataset, etc.
    
    workspace_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)
    conversation_id = Column(String, nullable=True, index=True)
    dataset_id = Column(String, nullable=True, index=True)
    context_id = Column(String, nullable=True, index=True)
    
    summary = Column(Text, nullable=False)
    importance_score = Column(Float, default=0.5)
    recency_score = Column(Float, default=1.0)
    confidence = Column(Float, default=1.0)
    
    evidence_references = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    is_archived = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    history = relationship("MemoryHistory", back_populates="memory", cascade="all, delete-orphan")
    versions = relationship("MemoryVersion", back_populates="memory", cascade="all, delete-orphan")
    metadata_entries = relationship("MemoryMetadata", back_populates="memory", cascade="all, delete-orphan")

class MemoryHistory(Base):
    """Tracks historical state changes to a memory."""
    __tablename__ = "memory_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    memory_id = Column(String, ForeignKey("memory_objects.id", ondelete="CASCADE"))
    action = Column(String, nullable=False) # CREATED, UPDATED, ARCHIVED, RESTORED
    previous_summary = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    memory = relationship("MemoryObject", back_populates="history")

class MemoryVersion(Base):
    """Versioning for specific memory objects."""
    __tablename__ = "memory_versions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    memory_id = Column(String, ForeignKey("memory_objects.id", ondelete="CASCADE"))
    version_number = Column(Integer, nullable=False)
    summary_snapshot = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    memory = relationship("MemoryObject", back_populates="versions")

class MemorySummary(Base):
    """Consolidated summaries generated from multiple raw memories."""
    __tablename__ = "memory_summaries"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=False) # E.g., conversation_id or user_id
    entity_type = Column(String, nullable=False)
    consolidated_summary = Column(Text, nullable=False)
    source_memory_ids = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class MemoryPolicy(Base):
    """Workspace-level rules for retention, expiration, and isolation."""
    __tablename__ = "memory_policies"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, unique=True)
    retention_days = Column(Integer, default=365)
    max_memory_size_mb = Column(Integer, default=100)
    priority_rules = Column(JSON, nullable=True)
    compliance_rules = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MemoryMetadata(Base):
    """Flexible key-value storage for metadata attached to memories."""
    __tablename__ = "memory_metadata"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    memory_id = Column(String, ForeignKey("memory_objects.id", ondelete="CASCADE"))
    key = Column(String, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    
    memory = relationship("MemoryObject", back_populates="metadata_entries")

class MemoryAudit(Base):
    """Tracks access and security compliance for memories."""
    __tablename__ = "memory_audit"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    operation = Column(String, nullable=False) # READ, WRITE, DELETE, SEARCH
    user_id = Column(String, nullable=True)
    memory_id = Column(String, nullable=True)
    status = Column(String, nullable=False) # SUCCESS, DENIED, FAILED
    timestamp = Column(DateTime, default=datetime.utcnow)

class MemoryMetrics(Base):
    """Observability model tracking metrics."""
    __tablename__ = "memory_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    operation = Column(String, nullable=False) # RETRIEVAL, WRITE, ARCHIVE, EXPIRATION
    latency_ms = Column(Integer, nullable=False)
    item_count = Column(Integer, nullable=False)
    cache_hit = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
