from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, JSON, DateTime, Enum, Index
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from app.core.database import Base

class ObjectStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DEPRECATED = "DEPRECATED"
    FAILED = "FAILED"
    PENDING = "PENDING"

class ValidationStatus(str, enum.Enum):
    VALIDATED = "VALIDATED"
    INVALID = "INVALID"
    PENDING = "PENDING"
    WARNING = "WARNING"

class AnalyticsObject(Base):
    __tablename__ = "analytics_objects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    object_type = Column(String, nullable=False)
    workspace_id = Column(String, nullable=False)
    dataset_id = Column(String, nullable=True)
    dataset_version_id = Column(String, nullable=True)
    pipeline_run_id = Column(String, nullable=True)
    
    engine_name = Column(String, nullable=False)
    engine_version = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=False)
    
    status = Column(Enum(ObjectStatus), default=ObjectStatus.ACTIVE)
    validation_status = Column(Enum(ValidationStatus), default=ValidationStatus.PENDING)
    
    confidence_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    business_domain = Column(String, nullable=True)
    
    payload = Column(JSON, nullable=False)
    
    metadata_info = relationship("ObjectMetadata", back_populates="analytics_object", uselist=False, cascade="all, delete-orphan")
    tags = relationship("ObjectTag", back_populates="analytics_object", cascade="all, delete-orphan")
    validations = relationship("ObjectValidation", back_populates="analytics_object", cascade="all, delete-orphan")
    history = relationship("ObjectHistory", back_populates="analytics_object", cascade="all, delete-orphan")
    versions = relationship("ObjectVersion", back_populates="analytics_object", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_analytics_objects_workspace', 'workspace_id'),
        Index('ix_analytics_objects_dataset', 'dataset_id'),
        Index('ix_analytics_objects_type', 'object_type'),
    )

class ObjectMetadata(Base):
    __tablename__ = "object_metadata"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = Column(String, ForeignKey("analytics_objects.id", ondelete="CASCADE"), nullable=False, unique=True)
    metadata_json = Column(JSON, nullable=False)
    
    analytics_object = relationship("AnalyticsObject", back_populates="metadata_info")

class ObjectDependency(Base):
    __tablename__ = "object_dependencies"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_object_id = Column(String, ForeignKey("analytics_objects.id", ondelete="CASCADE"), nullable=False)
    target_object_id = Column(String, ForeignKey("analytics_objects.id", ondelete="CASCADE"), nullable=False)
    dependency_type = Column(String, nullable=False)  # e.g., "generated_from", "uses"
    
    __table_args__ = (
        Index('ix_obj_deps_source', 'source_object_id'),
        Index('ix_obj_deps_target', 'target_object_id'),
    )

class ObjectVersion(Base):
    __tablename__ = "object_versions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = Column(String, ForeignKey("analytics_objects.id", ondelete="CASCADE"), nullable=False)
    major_version = Column(Integer, nullable=False, default=1)
    minor_version = Column(Integer, nullable=False, default=0)
    payload_snapshot = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    analytics_object = relationship("AnalyticsObject", back_populates="versions")

class ObjectHistory(Base):
    __tablename__ = "object_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = Column(String, ForeignKey("analytics_objects.id", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False) # CREATED, UPDATED, ARCHIVED
    actor_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, nullable=True)
    
    analytics_object = relationship("AnalyticsObject", back_populates="history")

class ObjectValidation(Base):
    __tablename__ = "object_validations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = Column(String, ForeignKey("analytics_objects.id", ondelete="CASCADE"), nullable=False)
    validator_name = Column(String, nullable=False)
    is_valid = Column(Boolean, nullable=False)
    errors = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    analytics_object = relationship("AnalyticsObject", back_populates="validations")

class ObjectRelationship(Base):
    __tablename__ = "object_relationships"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String, ForeignKey("analytics_objects.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(String, ForeignKey("analytics_objects.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String, nullable=False)

class ObjectTag(Base):
    __tablename__ = "object_tags"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = Column(String, ForeignKey("analytics_objects.id", ondelete="CASCADE"), nullable=False)
    tag_name = Column(String, nullable=False)
    
    analytics_object = relationship("AnalyticsObject", back_populates="tags")

class ObjectAudit(Base):
    __tablename__ = "object_audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata_snapshot = Column(JSON, nullable=True)

class RegistryStatistics(Base):
    __tablename__ = "registry_statistics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, nullable=False, unique=True)
    total_objects = Column(Integer, default=0)
    objects_by_type = Column(JSON, default=dict)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
