from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Text, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class RecommendationObject(Base):
    """Core entity for business recommendations."""
    __tablename__ = "recommendation_objects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    dataset_id = Column(String, nullable=True, index=True)
    insight_id = Column(String, nullable=False, index=True)
    
    business_domain = Column(String, nullable=False)
    recommendation_type = Column(String, nullable=False) # e.g. "Revenue Optimization"
    
    title = Column(String, nullable=False)
    executive_summary = Column(Text, nullable=False)
    detailed_recommendation = Column(Text, nullable=False)
    
    expected_benefit = Column(String, nullable=False)
    estimated_risk = Column(String, nullable=False)
    estimated_cost = Column(String, nullable=False)
    
    implementation_difficulty = Column(String, nullable=False) # LOW, MEDIUM, HIGH
    confidence_score = Column(Float, nullable=False, default=1.0)
    priority = Column(Integer, nullable=False, default=5)
    owner = Column(String, nullable=True)
    
    status = Column(String, nullable=False, default="OPEN") # OPEN, ARCHIVED
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    references = relationship("RecommendationReference", back_populates="recommendation", cascade="all, delete-orphan")
    histories = relationship("RecommendationIntelligenceHistory", back_populates="recommendation", cascade="all, delete-orphan")
    validations = relationship("RecommendationValidation", back_populates="recommendation", cascade="all, delete-orphan")
    scenarios = relationship("RecommendationScenario", back_populates="recommendation", cascade="all, delete-orphan")
    action_plan = relationship("RecommendationActionPlan", uselist=False, back_populates="recommendation", cascade="all, delete-orphan")

class RecommendationActionPlan(Base):
    """Structured action plan."""
    __tablename__ = "recommendation_action_plans"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    recommendation_id = Column(String, ForeignKey("recommendation_objects.id", ondelete="CASCADE"))
    
    immediate_actions = Column(JSON, nullable=False)
    short_term_actions = Column(JSON, nullable=False)
    medium_term_actions = Column(JSON, nullable=False)
    long_term_actions = Column(JSON, nullable=False)
    
    dependencies = Column(JSON, nullable=True)
    required_resources = Column(JSON, nullable=True)
    success_metrics = Column(JSON, nullable=True)
    kpis_to_monitor = Column(JSON, nullable=True)
    
    recommendation = relationship("RecommendationObject", back_populates="action_plan")

class RecommendationScenario(Base):
    """Best/Expected/Worst case scenarios."""
    __tablename__ = "recommendation_scenarios"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    recommendation_id = Column(String, ForeignKey("recommendation_objects.id", ondelete="CASCADE"))
    
    scenario_type = Column(String, nullable=False) # BEST_CASE, EXPECTED_CASE, WORST_CASE
    description = Column(Text, nullable=False)
    financial_impact = Column(Float, nullable=False)
    operational_impact = Column(String, nullable=True)
    strategic_impact = Column(String, nullable=True)
    
    recommendation = relationship("RecommendationObject", back_populates="scenarios")

class RecommendationReference(Base):
    """Maps recommendation to supporting evidence/insight objects."""
    __tablename__ = "recommendation_references"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    recommendation_id = Column(String, ForeignKey("recommendation_objects.id", ondelete="CASCADE"))
    
    reference_type = Column(String, nullable=False) # INSIGHT, EVIDENCE, CONTEXT
    reference_id = Column(String, nullable=False)
    
    recommendation = relationship("RecommendationObject", back_populates="references")

class RecommendationIntelligenceHistory(Base):
    """Lifecycle events."""
    __tablename__ = "rec_intel_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    recommendation_id = Column(String, ForeignKey("recommendation_objects.id", ondelete="CASCADE"))
    
    event = Column(String, nullable=False) # GENERATED, ARCHIVED
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    recommendation = relationship("RecommendationObject", back_populates="histories")

class RecommendationPriority(Base):
    """Scoring matrix."""
    __tablename__ = "recommendation_priorities"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    recommendation_id = Column(String, ForeignKey("recommendation_objects.id", ondelete="CASCADE"))
    
    business_value = Column(Float, nullable=False, default=0.0)
    roi = Column(Float, nullable=False, default=0.0)
    urgency = Column(Float, nullable=False, default=0.0)
    implementation_complexity = Column(Float, nullable=False, default=0.0)
    strategic_importance = Column(Float, nullable=False, default=0.0)
    
    final_score = Column(Float, nullable=False, default=0.0)

class RecommendationValidation(Base):
    """Rules validation output."""
    __tablename__ = "recommendation_validations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    recommendation_id = Column(String, ForeignKey("recommendation_objects.id", ondelete="CASCADE"))
    
    is_valid = Column(Boolean, nullable=False, default=False)
    validation_notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    recommendation = relationship("RecommendationObject", back_populates="validations")

class RecommendationAudit(Base):
    """Access logs."""
    __tablename__ = "recommendation_audit"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    recommendation_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False) 
    timestamp = Column(DateTime, default=datetime.utcnow)

class RecommendationMetrics(Base):
    """Observability metrics."""
    __tablename__ = "recommendation_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=True)
    generation_time_ms = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    roi = Column(Float, nullable=False)
    passed_validation = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
