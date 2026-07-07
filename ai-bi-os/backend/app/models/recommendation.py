from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, Text, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Recommendation(Base):
    """Core recommendation object generated from a Decision."""
    __tablename__ = "recommendations"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, nullable=False)
    decision_id = Column(String, ForeignKey("decisions.id"), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    business_domain = Column(String, nullable=False)
    category = Column(String, nullable=False) # e.g. REVENUE_GROWTH, COST_OPTIMIZATION
    
    priority = Column(String, default="MEDIUM")
    severity = Column(String, default="MEDIUM")
    
    roi_estimate = Column(Float, nullable=True) # % or absolute value
    estimated_cost = Column(Float, nullable=True)
    implementation_effort = Column(String, nullable=True) # HIGH, MEDIUM, LOW
    timeline = Column(String, nullable=True) # IMMEDIATE, SHORT_TERM, MEDIUM_TERM, LONG_TERM
    
    affected_kpis = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    status = Column(String, default="NEW") # NEW, APPROVED, REJECTED, EXECUTING, COMPLETED
    
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    score = relationship("RecommendationScore", uselist=False, back_populates="recommendation", cascade="all, delete-orphan")
    evidence = relationship("RecommendationEvidence", back_populates="recommendation", cascade="all, delete-orphan")
    action_plan = relationship("ActionPlan", uselist=False, back_populates="recommendation", cascade="all, delete-orphan")
    scenarios = relationship("ScenarioAnalysis", back_populates="recommendation", cascade="all, delete-orphan")
    impact_estimation = relationship("ImpactEstimation", uselist=False, back_populates="recommendation", cascade="all, delete-orphan")
    history = relationship("RecommendationHistory", back_populates="recommendation", cascade="all, delete-orphan")

class RecommendationScore(Base):
    """Scoring for prioritization."""
    __tablename__ = "recommendation_scores"
    id = Column(String, primary_key=True, default=generate_uuid)
    recommendation_id = Column(String, ForeignKey("recommendations.id"))
    
    final_score = Column(Float, nullable=False)
    priority_score = Column(Float, nullable=True)
    roi_score = Column(Float, nullable=True)
    business_value_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    urgency_score = Column(Float, nullable=True)
    feasibility_score = Column(Float, nullable=True)
    
    recommendation = relationship("Recommendation", back_populates="score")

class RecommendationEvidence(Base):
    """Traceability links."""
    __tablename__ = "recommendation_evidence"
    id = Column(String, primary_key=True, default=generate_uuid)
    recommendation_id = Column(String, ForeignKey("recommendations.id"))
    
    evidence_type = Column(String, nullable=False) # e.g. DECISION, RULE, INSIGHT
    reference_id = Column(String, nullable=True)
    description = Column(String, nullable=True)
    
    recommendation = relationship("Recommendation", back_populates="evidence")

class ActionPlan(Base):
    """Roadmap container for a recommendation."""
    __tablename__ = "action_plans"
    id = Column(String, primary_key=True, default=generate_uuid)
    recommendation_id = Column(String, ForeignKey("recommendations.id"))
    
    title = Column(String, nullable=False)
    business_objective = Column(String, nullable=True)
    expected_outcome = Column(String, nullable=True)
    success_metrics = Column(JSON, nullable=True)
    
    recommendation = relationship("Recommendation", back_populates="action_plan")
    steps = relationship("ActionStep", back_populates="action_plan", cascade="all, delete-orphan", order_by="ActionStep.order_index")

class ActionStep(Base):
    """Discrete step in an action plan."""
    __tablename__ = "action_steps"
    id = Column(String, primary_key=True, default=generate_uuid)
    action_plan_id = Column(String, ForeignKey("action_plans.id"))
    
    order_index = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    estimated_duration = Column(String, nullable=True)
    difficulty = Column(String, nullable=True)
    dependencies = Column(JSON, nullable=True)
    prerequisites = Column(JSON, nullable=True)
    
    action_plan = relationship("ActionPlan", back_populates="steps")

class ScenarioAnalysis(Base):
    """What-if simulations."""
    __tablename__ = "scenario_analyses"
    id = Column(String, primary_key=True, default=generate_uuid)
    recommendation_id = Column(String, ForeignKey("recommendations.id"))
    
    scenario_type = Column(String, nullable=False) # BEST_CASE, EXPECTED_CASE, WORST_CASE
    description = Column(String, nullable=True)
    estimated_roi = Column(Float, nullable=True)
    
    recommendation = relationship("Recommendation", back_populates="scenarios")

class ImpactEstimation(Base):
    """Financial/operational impact."""
    __tablename__ = "impact_estimations"
    id = Column(String, primary_key=True, default=generate_uuid)
    recommendation_id = Column(String, ForeignKey("recommendations.id"))
    
    revenue_increase = Column(Float, nullable=True)
    cost_reduction = Column(Float, nullable=True)
    profit_improvement = Column(Float, nullable=True)
    productivity_gain = Column(Float, nullable=True)
    risk_reduction = Column(Float, nullable=True)
    
    recommendation = relationship("Recommendation", back_populates="impact_estimation")

class RecommendationHistory(Base):
    """Lifecycle tracking."""
    __tablename__ = "recommendation_history"
    id = Column(String, primary_key=True, default=generate_uuid)
    recommendation_id = Column(String, ForeignKey("recommendations.id"))
    
    status = Column(String, nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(String, nullable=True)
    
    recommendation = relationship("Recommendation", back_populates="history")

class RecommendationDependency(Base):
    """Dependencies between recommendations."""
    __tablename__ = "recommendation_dependencies"
    id = Column(String, primary_key=True, default=generate_uuid)
    parent_id = Column(String, ForeignKey("recommendations.id"))
    child_id = Column(String, ForeignKey("recommendations.id"))
    
    dependency_type = Column(String, nullable=False) # BLOCKS, REQUIRES
