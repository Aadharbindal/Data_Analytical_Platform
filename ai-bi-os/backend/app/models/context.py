from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, Text, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class ContextObject(Base):
    """The structured Context Object built from Analytics Objects."""
    __tablename__ = "context_objects"
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    dataset_id = Column(String, nullable=True, index=True)
    dataset_version = Column(String, nullable=True)
    conversation_id = Column(String, nullable=True, index=True)
    request_id = Column(String, nullable=True, index=True)
    
    context_purpose = Column(String, nullable=True)
    business_domain = Column(String, nullable=True)
    
    context_payload = Column(JSON, nullable=False)
    
    generated_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    versions = relationship("ContextVersion", back_populates="context_object", cascade="all, delete-orphan")
    metadata_info = relationship("ContextMetadata", back_populates="context_object", cascade="all, delete-orphan")
    references = relationship("ContextReference", back_populates="context_object", cascade="all, delete-orphan")
    dependencies = relationship("ContextDependency", back_populates="context_object", cascade="all, delete-orphan")
    policies = relationship("ContextPolicy", back_populates="context_object", cascade="all, delete-orphan")
    history = relationship("ContextHistory", back_populates="context_object", cascade="all, delete-orphan")

class ContextVersion(Base):
    """Tracks context versions."""
    __tablename__ = "context_versions"
    id = Column(String, primary_key=True, default=generate_uuid)
    context_id = Column(String, ForeignKey("context_objects.id", ondelete="CASCADE"), nullable=False)
    
    version_number = Column(Integer, nullable=False, default=1)
    snapshot = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    context_object = relationship("ContextObject", back_populates="versions")

class ContextMetadata(Base):
    """Metadata about the context."""
    __tablename__ = "context_metadata"
    id = Column(String, primary_key=True, default=generate_uuid)
    context_id = Column(String, ForeignKey("context_objects.id", ondelete="CASCADE"), nullable=False)
    
    metadata_key = Column(String, nullable=False)
    metadata_value = Column(JSON, nullable=False)
    
    context_object = relationship("ContextObject", back_populates="metadata_info")

class ContextReference(Base):
    """References back to Analytics Objects."""
    __tablename__ = "context_references"
    id = Column(String, primary_key=True, default=generate_uuid)
    context_id = Column(String, ForeignKey("context_objects.id", ondelete="CASCADE"), nullable=False)
    
    analytics_object_id = Column(String, nullable=False, index=True)
    relevance_score = Column(Float, nullable=True)
    
    context_object = relationship("ContextObject", back_populates="references")

class ContextDependency(Base):
    """Dependencies on datasets or other contexts."""
    __tablename__ = "context_dependencies"
    id = Column(String, primary_key=True, default=generate_uuid)
    context_id = Column(String, ForeignKey("context_objects.id", ondelete="CASCADE"), nullable=False)
    
    dependency_type = Column(String, nullable=False) # e.g., 'DATASET', 'ANALYTICS_OBJECT', 'CONTEXT'
    dependency_id = Column(String, nullable=False)
    
    context_object = relationship("ContextObject", back_populates="dependencies")

class ContextPolicy(Base):
    """Policies applied to the context."""
    __tablename__ = "context_policies"
    id = Column(String, primary_key=True, default=generate_uuid)
    context_id = Column(String, ForeignKey("context_objects.id", ondelete="CASCADE"), nullable=False)
    
    policy_name = Column(String, nullable=False)
    policy_value = Column(String, nullable=False)
    enforced_at = Column(DateTime, default=datetime.utcnow)
    
    context_object = relationship("ContextObject", back_populates="policies")

class ContextHistory(Base):
    """Audit trail for context builds."""
    __tablename__ = "context_history"
    id = Column(String, primary_key=True, default=generate_uuid)
    context_id = Column(String, ForeignKey("context_objects.id", ondelete="CASCADE"), nullable=False)
    
    action = Column(String, nullable=False) # e.g., 'BUILT', 'REBUILT', 'VALIDATED'
    actor = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, nullable=True)
    
    context_object = relationship("ContextObject", back_populates="history")

class ContextCache(Base):
    """Caching metadata for quick retrieval."""
    __tablename__ = "context_caches"
    id = Column(String, primary_key=True, default=generate_uuid)
    cache_key = Column(String, nullable=False, unique=True, index=True)
    
    context_id = Column(String, ForeignKey("context_objects.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    context_object = relationship("ContextObject")
