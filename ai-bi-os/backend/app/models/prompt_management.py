from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Text, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class PromptRegistry(Base):
    """Central registry cataloging all prompt templates."""
    __tablename__ = "pm_prompt_registries"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    prompt_type = Column(String, nullable=False) # Analytics, SQL, Agent, etc.
    
    templates = relationship("PromptTemplate", back_populates="registry", cascade="all, delete-orphan")

class PromptTemplate(Base):
    """The structural reusable template with dynamic variables."""
    __tablename__ = "pm_prompt_templates"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    registry_id = Column(String, ForeignKey("pm_prompt_registries.id", ondelete="CASCADE"))
    
    template_structure = Column(JSON, nullable=False) # Sections and defaults
    variables = Column(JSON, nullable=False) # e.g. ["user_name", "date"]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    registry = relationship("PromptRegistry", back_populates="templates")
    versions = relationship("PromptVersion", back_populates="template", cascade="all, delete-orphan")

class PromptVersion(Base):
    """Specific iteration of a template."""
    __tablename__ = "pm_prompt_versions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    template_id = Column(String, ForeignKey("pm_prompt_templates.id", ondelete="CASCADE"))
    parent_version_id = Column(String, ForeignKey("pm_prompt_versions.id"), nullable=True)
    
    version_string = Column(String, nullable=False) # e.g. "1.2.0"
    is_major = Column(Boolean, default=False)
    
    content = Column(JSON, nullable=False) # The actual prompt payload definition for this version
    estimated_tokens = Column(Integer, default=0)
    
    author_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    template = relationship("PromptTemplate", back_populates="versions")
    lifecycle = relationship("PromptLifecycle", uselist=False, back_populates="version", cascade="all, delete-orphan")
    approvals = relationship("PromptApproval", back_populates="version", cascade="all, delete-orphan")
    diffs = relationship("PromptDiff", back_populates="version", cascade="all, delete-orphan")

class PromptLifecycle(Base):
    """State machine tracking the prompt's journey."""
    __tablename__ = "pm_prompt_lifecycles"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    version_id = Column(String, ForeignKey("pm_prompt_versions.id", ondelete="CASCADE"), unique=True)
    
    status = Column(String, nullable=False, default="DRAFT") # DRAFT, REVIEW, APPROVED, PUBLISHED, DEPRECATED, ARCHIVED
    published_at = Column(DateTime, nullable=True)
    rollback_reference = Column(String, nullable=True)
    
    version = relationship("PromptVersion", back_populates="lifecycle")

class PromptApproval(Base):
    """Workflow state for reviews and approvals."""
    __tablename__ = "pm_prompt_approvals"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    version_id = Column(String, ForeignKey("pm_prompt_versions.id", ondelete="CASCADE"))
    
    status = Column(String, nullable=False, default="PENDING")
    approver_id = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    version = relationship("PromptVersion", back_populates="approvals")
    reviews = relationship("PromptReview", back_populates="approval", cascade="all, delete-orphan")

class PromptReview(Base):
    """Feedback from peer or technical reviews."""
    __tablename__ = "pm_prompt_reviews"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    approval_id = Column(String, ForeignKey("pm_prompt_approvals.id", ondelete="CASCADE"))
    
    reviewer_id = Column(String, nullable=False)
    comments = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    approval = relationship("PromptApproval", back_populates="reviews")

class PromptDiff(Base):
    """Stored comparisons between this version and its parent."""
    __tablename__ = "pm_prompt_diffs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    version_id = Column(String, ForeignKey("pm_prompt_versions.id", ondelete="CASCADE"))
    
    added_sections = Column(JSON, nullable=True)
    removed_sections = Column(JSON, nullable=True)
    modified_sections = Column(JSON, nullable=True)
    token_delta = Column(Integer, default=0)
    
    version = relationship("PromptVersion", back_populates="diffs")

class PromptPolicy(Base):
    """Governance rules specific to prompt management."""
    __tablename__ = "pm_prompt_policies"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    
    policy_name = Column(String, nullable=False)
    policy_type = Column(String, nullable=False) # Security, Compliance, Business
    rules = Column(JSON, nullable=False)

class PromptManagementAudit(Base):
    """Immutable log of who did what in prompt management."""
    __tablename__ = "pm_prompt_audits"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    version_id = Column(String, nullable=True, index=True)
    
    actor_id = Column(String, nullable=False)
    action = Column(String, nullable=False) # CREATED, EDITED, REVIEWED, APPROVED, PUBLISHED, ROLLED_BACK
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
