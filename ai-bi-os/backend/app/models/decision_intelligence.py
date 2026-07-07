from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Text, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class DecisionObject(Base):
    """Core entity for structured business decisions."""
    __tablename__ = "decision_objects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    dataset_id = Column(String, nullable=True, index=True)
    
    decision_type = Column(String, nullable=False) # e.g. "Strategic Decision"
    business_objective = Column(String, nullable=False)
    
    decision_summary = Column(Text, nullable=False)
    selected_strategy = Column(Text, nullable=False)
    
    expected_roi = Column(Float, nullable=False)
    expected_revenue_impact = Column(Float, nullable=False)
    expected_cost_impact = Column(Float, nullable=False)
    expected_risk = Column(String, nullable=False) # LOW, MEDIUM, HIGH
    
    confidence_score = Column(Float, nullable=False, default=1.0)
    business_priority = Column(Integer, nullable=False, default=5)
    
    owner = Column(String, nullable=True)
    approval_status = Column(String, nullable=False, default="DRAFT") # DRAFT, REVIEW, PENDING_APPROVAL, APPROVED, REJECTED, EXECUTED, ARCHIVED
    
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    references = relationship("DecisionReference", back_populates="decision", cascade="all, delete-orphan")
    scenarios = relationship("DecisionScenario", back_populates="decision", cascade="all, delete-orphan")
    comparisons = relationship("DecisionComparison", back_populates="decision", cascade="all, delete-orphan")
    policies = relationship("DecisionPolicy", back_populates="decision", cascade="all, delete-orphan")
    approvals = relationship("DecisionApproval", back_populates="decision", cascade="all, delete-orphan")
    histories = relationship("DecisionIntelligenceHistory", back_populates="decision", cascade="all, delete-orphan")

class DecisionReference(Base):
    """Maps decision to supporting recommendation/insight objects."""
    __tablename__ = "decision_references"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    decision_id = Column(String, ForeignKey("decision_objects.id", ondelete="CASCADE"))
    
    reference_type = Column(String, nullable=False) # RECOMMENDATION, INSIGHT, EVIDENCE
    reference_id = Column(String, nullable=False)
    
    decision = relationship("DecisionObject", back_populates="references")

class DecisionScenario(Base):
    """Scenario projections for the decision."""
    __tablename__ = "decision_scenarios"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    decision_id = Column(String, ForeignKey("decision_objects.id", ondelete="CASCADE"))
    
    scenario_type = Column(String, nullable=False) # OPTIMISTIC, CONSERVATIVE, EXPECTED, BEST, WORST
    description = Column(Text, nullable=False)
    
    financial_projection = Column(Float, nullable=False)
    operational_projection = Column(String, nullable=True)
    strategic_projection = Column(String, nullable=True)
    
    decision = relationship("DecisionObject", back_populates="scenarios")

class DecisionComparison(Base):
    """Alternative strategies considered."""
    __tablename__ = "decision_comparisons"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    decision_id = Column(String, ForeignKey("decision_objects.id", ondelete="CASCADE"))
    
    strategy_name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    estimated_roi = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    
    decision = relationship("DecisionObject", back_populates="comparisons")

class DecisionPolicy(Base):
    """Organizational constraints applied."""
    __tablename__ = "decision_policies"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    decision_id = Column(String, ForeignKey("decision_objects.id", ondelete="CASCADE"))
    
    policy_name = Column(String, nullable=False)
    constraint_type = Column(String, nullable=False) # BUDGET, TIMELINE, RISK, COMPLIANCE
    constraint_value = Column(String, nullable=False)
    is_satisfied = Column(Boolean, nullable=False, default=True)
    
    decision = relationship("DecisionObject", back_populates="policies")

class DecisionApproval(Base):
    """Approval workflow states."""
    __tablename__ = "decision_approvals"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    decision_id = Column(String, ForeignKey("decision_objects.id", ondelete="CASCADE"))
    
    approver_id = Column(String, nullable=False)
    action = Column(String, nullable=False) # APPROVED, REJECTED, REQUESTED_CHANGES
    comments = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    decision = relationship("DecisionObject", back_populates="approvals")

class DecisionIntelligenceHistory(Base):
    """Lifecycle events."""
    __tablename__ = "dec_intel_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    decision_id = Column(String, ForeignKey("decision_objects.id", ondelete="CASCADE"))
    
    event = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    decision = relationship("DecisionObject", back_populates="histories")

class DecisionMetrics(Base):
    """Observability metrics."""
    __tablename__ = "decision_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=True)
    generation_time_ms = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    roi = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class DecisionAudit(Base):
    """Access logs."""
    __tablename__ = "decision_audit"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    decision_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False) 
    timestamp = Column(DateTime, default=datetime.utcnow)
