from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, Text, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class BusinessRule(Base):
    """Core rule definition."""
    __tablename__ = "business_rules"
    id = Column(String, primary_key=True, default=generate_uuid)
    
    workspace_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    business_domain = Column(String, nullable=False) # e.g. SALES, FINANCE
    priority = Column(String, default="MEDIUM") # CRITICAL, HIGH, MEDIUM, LOW
    severity = Column(String, default="MEDIUM")
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    condition = relationship("RuleCondition", uselist=False, back_populates="rule", cascade="all, delete-orphan")
    versions = relationship("RuleVersion", back_populates="rule", cascade="all, delete-orphan")
    executions = relationship("RuleExecution", back_populates="rule", cascade="all, delete-orphan")

class RuleCondition(Base):
    """AST representation of rule logic."""
    __tablename__ = "rule_conditions"
    id = Column(String, primary_key=True, default=generate_uuid)
    rule_id = Column(String, ForeignKey("business_rules.id"))
    
    ast = Column(JSON, nullable=False) # E.g., {"operator": "AND", "conditions": [{"field": "Insight.metric", "op": "==", "value": "Revenue"}, ...]}
    
    rule = relationship("BusinessRule", back_populates="condition")

class RuleVersion(Base):
    """Tracks historical versions of a rule."""
    __tablename__ = "rule_versions"
    id = Column(String, primary_key=True, default=generate_uuid)
    rule_id = Column(String, ForeignKey("business_rules.id"))
    
    version_number = Column(Integer, nullable=False)
    ast = Column(JSON, nullable=False)
    created_by = Column(String, nullable=True) # User ID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    rule = relationship("BusinessRule", back_populates="versions")

class RuleExecution(Base):
    """Log of a rule being executed."""
    __tablename__ = "rule_executions"
    id = Column(String, primary_key=True, default=generate_uuid)
    rule_id = Column(String, ForeignKey("business_rules.id"))
    dataset_version_id = Column(String, nullable=False)
    
    status = Column(String, nullable=False) # SUCCESS, FAILED
    evaluated_true = Column(Boolean, nullable=False)
    execution_time_ms = Column(Float, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)
    
    rule = relationship("BusinessRule", back_populates="executions")

class Decision(Base):
    """The actionable output when a rule evaluates to TRUE."""
    __tablename__ = "decisions"
    id = Column(String, primary_key=True, default=generate_uuid)
    
    dataset_version_id = Column(String, nullable=False)
    rule_id = Column(String, ForeignKey("business_rules.id"))
    insight_id = Column(String, ForeignKey("insights.id"), nullable=True) # The primary insight that triggered it
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    priority = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    business_domain = Column(String, nullable=False)
    
    affected_entities = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Simplified relationships
    history = relationship("DecisionHistory", back_populates="decision", cascade="all, delete-orphan")

class DecisionHistory(Base):
    """Tracks what happens to a decision over time (e.g. Actioned, Ignored)."""
    __tablename__ = "decision_history"
    id = Column(String, primary_key=True, default=generate_uuid)
    decision_id = Column(String, ForeignKey("decisions.id"))
    
    status = Column(String, nullable=False) # NEW, ACKNOWLEDGED, RESOLVED
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    decision = relationship("Decision", back_populates="history")

class RuleTemplate(Base):
    """Pre-defined rule structures for quick creation."""
    __tablename__ = "rule_templates"
    id = Column(String, primary_key=True, default=generate_uuid)
    
    name = Column(String, nullable=False)
    business_domain = Column(String, nullable=False)
    default_ast = Column(JSON, nullable=False)

class RuleAudit(Base):
    """Audit log for rule changes."""
    __tablename__ = "rule_audits"
    id = Column(String, primary_key=True, default=generate_uuid)
    rule_id = Column(String, nullable=False)
    
    action = Column(String, nullable=False) # CREATED, MODIFIED, DELETED
    user_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class RuleDependency(Base):
    """Links rules that trigger other rules."""
    __tablename__ = "rule_dependencies"
    id = Column(String, primary_key=True, default=generate_uuid)
    parent_rule_id = Column(String, ForeignKey("business_rules.id"))
    child_rule_id = Column(String, ForeignKey("business_rules.id"))
