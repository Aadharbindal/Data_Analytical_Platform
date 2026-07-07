from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Text, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Conversation(Base):
    """Core entity holding metadata for a conversation thread."""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)
    
    conversation_type = Column(String, nullable=False, default="General Business Chat")
    title = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    
    memory_references = Column(JSON, nullable=True)
    context_references = Column(JSON, nullable=True)
    evidence_references = Column(JSON, nullable=True)
    agent_references = Column(JSON, nullable=True)
    
    status = Column(String, default="OPEN") # OPEN, ARCHIVED, CLOSED
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions = relationship("ConversationSession", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")
    histories = relationship("ConversationHistory", back_populates="conversation", cascade="all, delete-orphan")

class ConversationSession(Base):
    """Tracks an active browsing session connected to a conversation."""
    __tablename__ = "conversation_sessions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"))
    workspace_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    
    context_version = Column(String, nullable=True)
    memory_version = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    agent_version = Column(String, nullable=True)
    
    status = Column(String, default="ACTIVE") # ACTIVE, ENDED, FAILED
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="sessions")
    states = relationship("ConversationState", back_populates="session", cascade="all, delete-orphan")

class ConversationMessage(Base):
    """Individual chat bubble."""
    __tablename__ = "conversation_messages"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"))
    
    role = Column(String, nullable=False) # user, assistant, system, tool, agent
    content = Column(Text, nullable=False)
    
    tokens_estimated = Column(Integer, nullable=True)
    tool_calls = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")

class ConversationState(Base):
    """Tracks the state machine for an active session (Planning, Executing, Streaming)."""
    __tablename__ = "conversation_states"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("conversation_sessions.id", ondelete="CASCADE"))
    
    state_name = Column(String, nullable=False) # IDLE, PLANNING, EXECUTING, WAITING, STREAMING, COMPLETED, FAILED, CANCELLED
    details = Column(JSON, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("ConversationSession", back_populates="states")

class ConversationHistory(Base):
    """Lifecycle events of the conversation."""
    __tablename__ = "conversation_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"))
    
    event = Column(String, nullable=False) # CREATE, PAUSE, RESUME, ARCHIVE, RESTORE
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="histories")

class ConversationSummary(Base):
    """Rolling summary of older messages."""
    __tablename__ = "conversation_summaries"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, nullable=False, index=True)
    summary_text = Column(Text, nullable=False)
    covered_message_ids = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ConversationMetadata(Base):
    """Arbitrary key-value store for context."""
    __tablename__ = "conversation_metadata"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, nullable=False, index=True)
    key = Column(String, nullable=False)
    value = Column(JSON, nullable=False)

class ConversationAudit(Base):
    """Access logs."""
    __tablename__ = "conversation_audit"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    conversation_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ConversationMetrics(Base):
    """Tracks duration, tokens, and stream latency."""
    __tablename__ = "conversation_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, nullable=True)
    metric_type = Column(String, nullable=False) # STREAMING_LATENCY, TOKEN_THROUGHPUT, DURATION
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
