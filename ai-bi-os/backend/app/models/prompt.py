from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, Text, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class PromptObject(Base):
    """The structured Prompt Object ready for LLM execution."""
    __tablename__ = "prompt_objects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    conversation_id = Column(String, nullable=True, index=True)
    request_id = Column(String, nullable=True, index=True)
    
    prompt_type = Column(String, nullable=False) # Analytics, SQL, Forecast, etc.
    prompt_version = Column(String, nullable=True, default="1.0")
    
    prompt_priority = Column(Integer, default=1)
    prompt_size = Column(Integer, default=0)
    estimated_tokens = Column(Integer, default=0)
    
    structured_prompt = Column(JSON, nullable=False) # Compiled prompt payload
    
    validation_status = Column(String, nullable=False, default="PENDING")
    
    created_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    metadata_info = relationship("PromptMetadata", back_populates="prompt_object", cascade="all, delete-orphan")
    sections = relationship("PromptSection", back_populates="prompt_object", cascade="all, delete-orphan")
    references = relationship("PromptReference", back_populates="prompt_object", cascade="all, delete-orphan")
    validations = relationship("PromptValidation", back_populates="prompt_object", cascade="all, delete-orphan")
    optimizations = relationship("PromptOptimization", back_populates="prompt_object", cascade="all, delete-orphan")
    history = relationship("PromptHistory", back_populates="prompt_object", cascade="all, delete-orphan")
    audits = relationship("PromptAudit", back_populates="prompt_object", cascade="all, delete-orphan")

class PromptMetadata(Base):
    __tablename__ = "prompt_metadata"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    prompt_id = Column(String, ForeignKey("prompt_objects.id", ondelete="CASCADE"), nullable=False)
    
    metadata_key = Column(String, nullable=False)
    metadata_value = Column(JSON, nullable=False)
    
    prompt_object = relationship("PromptObject", back_populates="metadata_info")

class PromptSection(Base):
    __tablename__ = "prompt_sections"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    prompt_id = Column(String, ForeignKey("prompt_objects.id", ondelete="CASCADE"), nullable=False)
    
    section_name = Column(String, nullable=False) # System Instructions, Context, Rules, etc.
    content = Column(Text, nullable=False)
    section_priority = Column(Integer, default=1)
    
    prompt_object = relationship("PromptObject", back_populates="sections")

class PromptReference(Base):
    __tablename__ = "prompt_references"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    prompt_id = Column(String, ForeignKey("prompt_objects.id", ondelete="CASCADE"), nullable=False)
    
    source_type = Column(String, nullable=False) # e.g. 'CONTEXT_OBJECT', 'EVIDENCE_OBJECT'
    source_id = Column(String, nullable=False, index=True)
    
    prompt_object = relationship("PromptObject", back_populates="references")

class PromptValidation(Base):
    __tablename__ = "prompt_validations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    prompt_id = Column(String, ForeignKey("prompt_objects.id", ondelete="CASCADE"), nullable=False)
    
    is_valid = Column(Boolean, default=True)
    validation_type = Column(String, nullable=False) # Missing Context, Policy Violation, Oversized
    details = Column(String, nullable=True)
    
    prompt_object = relationship("PromptObject", back_populates="validations")

class PromptOptimization(Base):
    __tablename__ = "prompt_optimizations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    prompt_id = Column(String, ForeignKey("prompt_objects.id", ondelete="CASCADE"), nullable=False)
    
    original_size = Column(Integer, nullable=False)
    optimized_size = Column(Integer, nullable=False)
    optimization_ratio = Column(Float, nullable=False)
    actions_taken = Column(JSON, nullable=True)
    
    prompt_object = relationship("PromptObject", back_populates="optimizations")

class PromptHistory(Base):
    __tablename__ = "prompt_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    prompt_id = Column(String, ForeignKey("prompt_objects.id", ondelete="CASCADE"), nullable=False)
    
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, nullable=True)
    
    prompt_object = relationship("PromptObject", back_populates="history")

class PromptAudit(Base):
    __tablename__ = "prompt_audits"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    prompt_id = Column(String, ForeignKey("prompt_objects.id", ondelete="CASCADE"), nullable=False)
    
    triggered_by = Column(String, nullable=True)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    prompt_object = relationship("PromptObject", back_populates="audits")
