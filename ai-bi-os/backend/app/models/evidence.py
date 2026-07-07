from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class EvidenceObject(Base):
    """Core evidence payload generated from Analytics and Context."""
    __tablename__ = "evidence_objects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    dataset_id = Column(String, nullable=True, index=True)
    dataset_version = Column(String, nullable=True)
    context_id = Column(String, nullable=False, index=True)
    
    evidence_type = Column(String, nullable=False) # e.g. StatisticalEvidence, KPIEvidence
    evidence_category = Column(String, nullable=False)
    evidence_priority = Column(Integer, default=0)
    
    evidence_confidence = Column(Float, nullable=False, default=0.0)
    business_confidence = Column(Float, nullable=False, default=0.0)
    validation_status = Column(String, nullable=False, default="PENDING")
    
    payload = Column(JSON, nullable=False) # Detailed evidence content
    
    created_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    metadata_info = relationship("EvidenceMetadata", back_populates="evidence_object", cascade="all, delete-orphan")
    references = relationship("EvidenceReference", back_populates="evidence_object", cascade="all, delete-orphan")
    scores = relationship("EvidenceScore", back_populates="evidence_object", cascade="all, delete-orphan")
    conflicts = relationship("EvidenceConflict", back_populates="evidence_object", cascade="all, delete-orphan")
    history = relationship("EvidenceHistory", back_populates="evidence_object", cascade="all, delete-orphan")
    policies = relationship("EvidencePolicy", back_populates="evidence_object", cascade="all, delete-orphan")

class EvidenceMetadata(Base):
    __tablename__ = "evidence_metadata"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    evidence_id = Column(String, ForeignKey("evidence_objects.id", ondelete="CASCADE"), nullable=False)
    
    metadata_key = Column(String, nullable=False)
    metadata_value = Column(JSON, nullable=False)
    
    evidence_object = relationship("EvidenceObject", back_populates="metadata_info")

class EvidenceReference(Base):
    __tablename__ = "evidence_references"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    evidence_id = Column(String, ForeignKey("evidence_objects.id", ondelete="CASCADE"), nullable=False)
    
    source_type = Column(String, nullable=False) # e.g., 'ANALYTICS_OBJECT', 'CONTEXT_OBJECT'
    source_id = Column(String, nullable=False, index=True)
    
    evidence_object = relationship("EvidenceObject", back_populates="references")

class EvidenceScore(Base):
    __tablename__ = "evidence_scores"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    evidence_id = Column(String, ForeignKey("evidence_objects.id", ondelete="CASCADE"), nullable=False)
    
    quality_score = Column(Float, nullable=True)
    freshness_score = Column(Float, nullable=True)
    reliability_score = Column(Float, nullable=True)
    completeness_score = Column(Float, nullable=True)
    consistency_score = Column(Float, nullable=True)
    business_relevance = Column(Float, nullable=True)
    
    evidence_object = relationship("EvidenceObject", back_populates="scores")

class EvidenceConflict(Base):
    __tablename__ = "evidence_conflicts"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    evidence_id = Column(String, ForeignKey("evidence_objects.id", ondelete="CASCADE"), nullable=False)
    
    conflict_type = Column(String, nullable=False)
    conflict_description = Column(String, nullable=False)
    conflicting_object_id = Column(String, nullable=True)
    resolved = Column(Boolean, default=False)
    
    evidence_object = relationship("EvidenceObject", back_populates="conflicts")

class EvidenceHistory(Base):
    __tablename__ = "evidence_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    evidence_id = Column(String, ForeignKey("evidence_objects.id", ondelete="CASCADE"), nullable=False)
    
    action = Column(String, nullable=False)
    actor = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, nullable=True)
    
    evidence_object = relationship("EvidenceObject", back_populates="history")

class EvidencePolicy(Base):
    __tablename__ = "evidence_policies"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    evidence_id = Column(String, ForeignKey("evidence_objects.id", ondelete="CASCADE"), nullable=False)
    
    policy_name = Column(String, nullable=False)
    policy_value = Column(String, nullable=False)
    enforced_at = Column(DateTime, default=datetime.utcnow)
    
    evidence_object = relationship("EvidenceObject", back_populates="policies")

class EvidenceAudit(Base):
    __tablename__ = "evidence_audits"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    evidence_id = Column(String, nullable=False, index=True)
    
    action = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    snapshot = Column(JSON, nullable=True)
