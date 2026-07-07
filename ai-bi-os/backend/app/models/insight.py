from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, Text, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Insight(Base):
    """Core insight object representing a deterministic business finding."""
    __tablename__ = "insights"
    id = Column(String, primary_key=True, default=generate_uuid)
    
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"), nullable=False)
    
    title = Column(String, nullable=False)
    category = Column(String, nullable=False) # e.g. ANOMALY, TREND, ROOT_CAUSE, OPPORTUNITY, RISK
    business_domain = Column(String, nullable=True) # e.g. SALES, MARKETING
    insight_type = Column(String, nullable=False) # e.g. SUDDEN_GROWTH, TOP_CONTRIBUTOR
    
    metric = Column(String, nullable=False) # E.g., Revenue
    affected_entities = Column(JSON, nullable=True) # e.g., ["Region: North"]
    
    severity = Column(String, nullable=True) # HIGH, MEDIUM, LOW
    status = Column(String, default="VALIDATED") # REJECTED, VALIDATED
    
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    evidence = relationship("InsightEvidence", back_populates="insight", cascade="all, delete-orphan")
    score = relationship("InsightScore", uselist=False, back_populates="insight", cascade="all, delete-orphan")
    ranking = relationship("InsightRanking", uselist=False, back_populates="insight", cascade="all, delete-orphan")
    validation = relationship("InsightValidation", uselist=False, back_populates="insight", cascade="all, delete-orphan")

class InsightEvidence(Base):
    """Backing data or references to raw analytics."""
    __tablename__ = "insight_evidence"
    id = Column(String, primary_key=True, default=generate_uuid)
    insight_id = Column(String, ForeignKey("insights.id"))
    
    evidence_type = Column(String, nullable=False) # e.g., VARIANCE_ID, SEGMENT_ID, CALCULATION
    reference_id = Column(String, nullable=True) # ID of the Analytics object
    data = Column(JSON, nullable=True) # Raw numbers supporting it
    
    insight = relationship("Insight", back_populates="evidence")

class InsightScore(Base):
    """Multi-dimensional scoring of the insight."""
    __tablename__ = "insight_scores"
    id = Column(String, primary_key=True, default=generate_uuid)
    insight_id = Column(String, ForeignKey("insights.id"))
    
    confidence = Column(Float, nullable=False) # 0.0 to 1.0
    business_impact = Column(Float, nullable=False) # 0.0 to 1.0
    urgency = Column(Float, nullable=False) # 0.0 to 1.0
    novelty = Column(Float, nullable=False) # 0.0 to 1.0
    statistical_significance = Column(Float, nullable=True) # p-value or similar
    
    insight = relationship("Insight", back_populates="score")

class InsightRanking(Base):
    """The final calculated rank for sorting insights for the user."""
    __tablename__ = "insight_rankings"
    id = Column(String, primary_key=True, default=generate_uuid)
    insight_id = Column(String, ForeignKey("insights.id"))
    
    final_score = Column(Float, nullable=False)
    rank_position = Column(Integer, nullable=True)
    
    insight = relationship("Insight", back_populates="ranking")

class InsightValidation(Base):
    """Tracks if an insight was rejected or validated, and why."""
    __tablename__ = "insight_validations"
    id = Column(String, primary_key=True, default=generate_uuid)
    insight_id = Column(String, ForeignKey("insights.id"))
    
    is_valid = Column(Boolean, default=True)
    rejection_reason = Column(String, nullable=True) # e.g., LOW_CONFIDENCE, DUPLICATE
    
    insight = relationship("Insight", back_populates="validation")
