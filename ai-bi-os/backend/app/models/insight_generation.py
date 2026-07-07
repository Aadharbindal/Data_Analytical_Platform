from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Text, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class InsightObject(Base):
    """Core insight entity tracking narrative and scores."""
    __tablename__ = "insight_objects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    dataset_id = Column(String, nullable=True, index=True)
    conversation_id = Column(String, nullable=True, index=True)
    
    insight_type = Column(String, nullable=False) # e.g. "Revenue Insights", "Trend Insights"
    business_domain = Column(String, nullable=False, default="General")
    
    headline = Column(String, nullable=False)
    detailed_narrative = Column(Text, nullable=False)
    
    confidence_score = Column(Float, nullable=False, default=1.0)
    business_impact_score = Column(Float, nullable=False, default=50.0)
    priority = Column(Integer, nullable=False, default=5)
    severity = Column(String, nullable=False, default="LOW") # LOW, MEDIUM, HIGH, CRITICAL
    
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    references = relationship("InsightReference", back_populates="insight", cascade="all, delete-orphan")
    histories = relationship("InsightHistory", back_populates="insight", cascade="all, delete-orphan")
    validations = relationship("InsightObjectValidation", back_populates="insight", cascade="all, delete-orphan")
    categories = relationship("InsightCategory", back_populates="insight", cascade="all, delete-orphan")

class InsightReference(Base):
    """Maps insight to specific objects (Evidence, Context, Analytics)."""
    __tablename__ = "insight_object_references"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    insight_id = Column(String, ForeignKey("insight_objects.id", ondelete="CASCADE"))
    
    reference_type = Column(String, nullable=False) # EVIDENCE, CONTEXT, ANALYTICS, FORECAST, KPI
    reference_id = Column(String, nullable=False)
    
    insight = relationship("InsightObject", back_populates="references")

class InsightHistory(Base):
    """Tracks changes over time to an insight."""
    __tablename__ = "insight_object_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    insight_id = Column(String, ForeignKey("insight_objects.id", ondelete="CASCADE"))
    
    action = Column(String, nullable=False) # GENERATED, REGENERATED, INVALIDATED
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    insight = relationship("InsightObject", back_populates="histories")

class InsightPriority(Base):
    """Configuration and scores determining the ranking of the insight."""
    __tablename__ = "insight_priorities"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    insight_id = Column(String, ForeignKey("insight_objects.id", ondelete="CASCADE"))
    
    financial_impact = Column(Float, nullable=False, default=0.0)
    operational_impact = Column(Float, nullable=False, default=0.0)
    strategic_importance = Column(Float, nullable=False, default=0.0)
    urgency = Column(Float, nullable=False, default=0.0)
    
    calculated_score = Column(Float, nullable=False, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

class InsightObjectValidation(Base):
    """Rules and status indicating if insight passed hallucination checks."""
    __tablename__ = "insight_object_validations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    insight_id = Column(String, ForeignKey("insight_objects.id", ondelete="CASCADE"))
    
    is_valid = Column(Boolean, nullable=False, default=False)
    validation_notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    insight = relationship("InsightObject", back_populates="validations")

class InsightCategory(Base):
    """Tagging and grouping constructs (e.g., Department, Dataset)."""
    __tablename__ = "insight_categories"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    insight_id = Column(String, ForeignKey("insight_objects.id", ondelete="CASCADE"))
    
    category_name = Column(String, nullable=False)
    
    insight = relationship("InsightObject", back_populates="categories")

class InsightAudit(Base):
    """Access logs for RBAC compliance."""
    __tablename__ = "insight_object_audit"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    insight_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False) # READ, DELETE, GENERATE
    timestamp = Column(DateTime, default=datetime.utcnow)

class InsightMetrics(Base):
    """Observability metrics for insight generation."""
    __tablename__ = "insight_object_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=True)
    generation_time_ms = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    business_impact = Column(Float, nullable=False)
    passed_validation = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
