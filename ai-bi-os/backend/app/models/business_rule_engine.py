from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Text, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class RuleDefinition(Base):
    """Core entity for a business rule definition."""
    __tablename__ = "business_rule_definitions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    department = Column(String, nullable=True)
    
    rule_name = Column(String, nullable=False)
    rule_category = Column(String, nullable=False) # Validation, Approval, Financial, Compliance
    description = Column(Text, nullable=False)
    
    priority = Column(Integer, nullable=False, default=5)
    severity = Column(String, nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    
    # The JSON-based Abstract Syntax Tree representing the conditions
    expression_ast = Column(JSON, nullable=False) 
    
    # Action to take when condition is met (Approve, Reject, Warn, Require Approval)
    action = Column(String, nullable=False) 
    
    status = Column(String, nullable=False, default="ACTIVE") # ACTIVE, INACTIVE, DRAFT
    version = Column(Integer, nullable=False, default=1)
    
    author = Column(String, nullable=True)
    reviewer = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    executions = relationship("RuleExecution", back_populates="rule", cascade="all, delete-orphan")
    versions = relationship("RuleVersion", back_populates="rule", cascade="all, delete-orphan")

class RuleVersion(Base):
    """Snapshot of a rule definition."""
    __tablename__ = "business_rule_versions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    rule_id = Column(String, ForeignKey("business_rule_definitions.id", ondelete="CASCADE"))
    
    version = Column(Integer, nullable=False)
    expression_ast = Column(JSON, nullable=False) 
    action = Column(String, nullable=False) 
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    rule = relationship("RuleDefinition", back_populates="versions")

class RuleExecution(Base):
    """Log of every rule evaluation."""
    __tablename__ = "business_rule_executions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    rule_id = Column(String, ForeignKey("business_rule_definitions.id", ondelete="CASCADE"))
    workspace_id = Column(String, nullable=False)
    
    input_objects = Column(JSON, nullable=False) # The payload that was evaluated
    evaluation_result = Column(String, nullable=False) # PASS, FAIL, ERROR
    triggered_action = Column(String, nullable=True) # What action was taken
    
    execution_time_ms = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    rule = relationship("RuleDefinition", back_populates="executions")

class RuleGroup(Base):
    """Logical grouping of rules for policies."""
    __tablename__ = "business_rule_groups"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    group_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

class RulePolicy(Base):
    """Mapping of rules to a group/policy."""
    __tablename__ = "business_rule_policies"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    group_id = Column(String, ForeignKey("business_rule_groups.id", ondelete="CASCADE"))
    rule_id = Column(String, ForeignKey("business_rule_definitions.id", ondelete="CASCADE"))
    is_mandatory = Column(Boolean, nullable=False, default=True)

class RuleAudit(Base):
    """Access and change logs for rules."""
    __tablename__ = "business_rule_audit"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    rule_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False) # CREATE, UPDATE, DELETE, PUBLISH
    timestamp = Column(DateTime, default=datetime.utcnow)

class RuleMetrics(Base):
    """Observability metrics for rule evaluation."""
    __tablename__ = "business_rule_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=True)
    rule_id = Column(String, nullable=False)
    execution_time_ms = Column(Integer, nullable=False)
    result = Column(String, nullable=False) # PASS, FAIL
    timestamp = Column(DateTime, default=datetime.utcnow)
