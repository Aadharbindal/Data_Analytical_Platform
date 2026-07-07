"""
Module 18: Enterprise AI Gateway — Database Models

Stores:
  AIProvider       — Provider config (OpenAI, Anthropic, etc.)
  AIModel          — Per-model metadata & pricing
  ModelCapability  — Task-type → model mappings
  ModelHealth      — Rolling health window per model
  ModelUsage       — Per-request token usage log
  ModelCost        — Per-day/workspace/user cost aggregations
  GatewayRequest   — Full audit log of every AI request
  GatewayResponse  — Response metadata (model, latency, tokens, fallback)
  ProviderPolicy   — Per-workspace routing rules & cost caps
"""

from sqlalchemy import (
    Column, String, Float, Boolean, ForeignKey,
    JSON, Integer, Text, DateTime, Enum as SAEnum
)
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from app.core.database import Base


def _uuid():
    return str(uuid.uuid4())


# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

class ProviderStatus(str, enum.Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class CircuitState(str, enum.Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Tripped — reject fast
    HALF_OPEN = "half_open"  # Testing with 1 request


class TaskType(str, enum.Enum):
    CHAT = "chat"
    REASONING = "reasoning"
    SQL_GENERATION = "sql_generation"
    SUMMARIZATION = "summarization"
    EXECUTIVE_REPORT = "executive_report"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    TRANSLATION = "translation"
    FORECAST_EXPLANATION = "forecast_explanation"
    ROOT_CAUSE = "root_cause"
    TECHNICAL_DOCUMENTATION = "technical_documentation"
    EMBEDDING = "embedding"
    GENERIC = "generic"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    FALLBACK_USED = "fallback_used"


# ─────────────────────────────────────────────────────────────
# AIProvider
# ─────────────────────────────────────────────────────────────

class AIProvider(Base):
    """Configuration for each supported AI provider."""
    __tablename__ = "ai_providers"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False, unique=True)       # e.g. "openai"
    display_name = Column(String, nullable=False)            # e.g. "OpenAI"
    base_url = Column(String, nullable=True)                 # Override for Azure / self-hosted
    auth_type = Column(String, default="bearer")             # bearer | api_key | oauth
    encrypted_api_key = Column(Text, nullable=True)          # Fernet-encrypted
    status = Column(SAEnum(ProviderStatus), default=ProviderStatus.ACTIVE)
    circuit_state = Column(SAEnum(CircuitState), default=CircuitState.CLOSED)
    circuit_failure_count = Column(Integer, default=0)
    circuit_last_failure = Column(DateTime, nullable=True)
    circuit_opened_at = Column(DateTime, nullable=True)
    priority = Column(Integer, default=100)                  # Lower = higher priority
    max_requests_per_minute = Column(Integer, default=500)
    supports_streaming = Column(Boolean, default=True)
    extra_config = Column(JSON, nullable=True)               # Provider-specific params
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    models = relationship("AIModel", back_populates="provider", cascade="all, delete-orphan")
    policies = relationship("ProviderPolicy", back_populates="provider")
    health_records = relationship("ModelHealth", back_populates="provider")


# ─────────────────────────────────────────────────────────────
# AIModel
# ─────────────────────────────────────────────────────────────

class AIModel(Base):
    """Full metadata for every registered model."""
    __tablename__ = "ai_models"

    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, nullable=False, unique=True)   # e.g. "gpt-4o"
    provider_id = Column(String, ForeignKey("ai_providers.id"), nullable=False)
    display_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Context & token limits
    context_window = Column(Integer, default=4096)
    max_input_tokens = Column(Integer, nullable=True)
    max_output_tokens = Column(Integer, nullable=True)

    # Capability flags
    supports_functions = Column(Boolean, default=False)
    supports_json_mode = Column(Boolean, default=False)
    supports_vision = Column(Boolean, default=False)
    supports_streaming = Column(Boolean, default=True)
    supports_embeddings = Column(Boolean, default=False)
    supports_reasoning = Column(Boolean, default=False)

    # Pricing (USD per 1M tokens)
    input_cost_per_1m = Column(Float, default=0.0)
    output_cost_per_1m = Column(Float, default=0.0)

    # Performance
    avg_latency_ms = Column(Float, nullable=True)
    p95_latency_ms = Column(Float, nullable=True)
    throughput_tokens_per_sec = Column(Integer, nullable=True)

    # Routing weights (0.0 – 1.0)
    accuracy_score = Column(Float, default=0.8)   # Quality proxy
    speed_score = Column(Float, default=0.8)
    cost_score = Column(Float, default=0.8)        # Inverse of price

    is_available = Column(Boolean, default=True)
    is_deprecated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    provider = relationship("AIProvider", back_populates="models")
    capabilities = relationship("ModelCapability", back_populates="model", cascade="all, delete-orphan")
    health_records = relationship("ModelHealth", back_populates="model")
    usage_records = relationship("ModelUsage", back_populates="model")


# ─────────────────────────────────────────────────────────────
# ModelCapability
# ─────────────────────────────────────────────────────────────

class ModelCapability(Base):
    """Maps task types to models with a suitability score."""
    __tablename__ = "model_capabilities"

    id = Column(String, primary_key=True, default=_uuid)
    model_id = Column(String, ForeignKey("ai_models.id"), nullable=False)
    task_type = Column(SAEnum(TaskType), nullable=False)
    suitability_score = Column(Float, default=0.8)   # 0.0 – 1.0
    is_preferred = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    model = relationship("AIModel", back_populates="capabilities")


# ─────────────────────────────────────────────────────────────
# ModelHealth
# ─────────────────────────────────────────────────────────────

class ModelHealth(Base):
    """Rolling health window snapshot per provider."""
    __tablename__ = "model_health"

    id = Column(String, primary_key=True, default=_uuid)
    provider_id = Column(String, ForeignKey("ai_providers.id"), nullable=False)
    model_id = Column(String, ForeignKey("ai_models.id"), nullable=True)

    is_available = Column(Boolean, default=True)
    latency_ms = Column(Float, nullable=True)
    p50_latency_ms = Column(Float, nullable=True)
    p95_latency_ms = Column(Float, nullable=True)
    error_rate = Column(Float, default=0.0)        # 0.0 – 1.0
    timeout_rate = Column(Float, default=0.0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_checked_at = Column(DateTime, default=datetime.utcnow)
    check_message = Column(String, nullable=True)

    provider = relationship("AIProvider", back_populates="health_records")
    model = relationship("AIModel", back_populates="health_records")


# ─────────────────────────────────────────────────────────────
# ModelUsage
# ─────────────────────────────────────────────────────────────

class ModelUsage(Base):
    """Per-request token usage ledger."""
    __tablename__ = "model_usage"

    id = Column(String, primary_key=True, default=_uuid)
    request_id = Column(String, nullable=False, index=True)
    model_id = Column(String, ForeignKey("ai_models.id"), nullable=False)
    workspace_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=True, index=True)

    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)

    task_type = Column(SAEnum(TaskType), nullable=True)
    latency_ms = Column(Float, nullable=True)
    was_cached = Column(Boolean, default=False)
    fallback_count = Column(Integer, default=0)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    model = relationship("AIModel", back_populates="usage_records")


# ─────────────────────────────────────────────────────────────
# ModelCost
# ─────────────────────────────────────────────────────────────

class ModelCost(Base):
    """Daily cost aggregations per workspace/user/provider."""
    __tablename__ = "model_costs"

    id = Column(String, primary_key=True, default=_uuid)
    date = Column(String, nullable=False, index=True)          # YYYY-MM-DD
    workspace_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=True)
    provider_name = Column(String, nullable=True)
    model_id_str = Column(String, nullable=True)

    total_requests = Column(Integer, default=0)
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────────────────────────
# GatewayRequest
# ─────────────────────────────────────────────────────────────

class GatewayRequest(Base):
    """Full audit log of every request entering the AI Gateway."""
    __tablename__ = "gateway_requests"

    id = Column(String, primary_key=True, default=_uuid)
    workspace_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=True)
    task_type = Column(SAEnum(TaskType), nullable=False)
    status = Column(SAEnum(RequestStatus), default=RequestStatus.PENDING)

    # The incoming prompt (optionally redacted)
    prompt_hash = Column(String, nullable=True)     # SHA-256 for dedup
    prompt_preview = Column(Text, nullable=True)    # First 200 chars (redacted)
    messages_count = Column(Integer, default=1)

    # Routing hints from caller
    required_capabilities = Column(JSON, nullable=True)
    max_cost_usd = Column(Float, nullable=True)
    max_latency_ms = Column(Float, nullable=True)
    preferred_provider = Column(String, nullable=True)
    preferred_model = Column(String, nullable=True)

    # Resolution
    resolved_provider = Column(String, nullable=True)
    resolved_model = Column(String, nullable=True)
    fallback_count = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    response = relationship("GatewayResponse", uselist=False, back_populates="request")


# ─────────────────────────────────────────────────────────────
# GatewayResponse
# ─────────────────────────────────────────────────────────────

class GatewayResponse(Base):
    """Response metadata returned with every AI completion."""
    __tablename__ = "gateway_responses"

    id = Column(String, primary_key=True, default=_uuid)
    request_id = Column(String, ForeignKey("gateway_requests.id"), nullable=False)

    content = Column(Text, nullable=True)           # Full completion text
    finish_reason = Column(String, nullable=True)   # stop | length | tool_calls
    model_used = Column(String, nullable=False)
    provider_used = Column(String, nullable=False)

    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Float, nullable=True)

    fallback_used = Column(Boolean, default=False)
    fallback_chain = Column(JSON, nullable=True)    # List of providers tried
    retry_count = Column(Integer, default=0)
    confidence_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    request = relationship("GatewayRequest", back_populates="response")


# ─────────────────────────────────────────────────────────────
# ProviderPolicy
# ─────────────────────────────────────────────────────────────

class ProviderPolicy(Base):
    """Per-workspace routing rules, cost caps, and provider permissions."""
    __tablename__ = "provider_policies"

    id = Column(String, primary_key=True, default=_uuid)
    workspace_id = Column(String, nullable=False, unique=True, index=True)
    provider_id = Column(String, ForeignKey("ai_providers.id"), nullable=True)

    allowed_providers = Column(JSON, nullable=True)          # ["openai", "anthropic"]
    blocked_providers = Column(JSON, nullable=True)          # ["openai"]
    preferred_provider = Column(String, nullable=True)
    preferred_model = Column(String, nullable=True)

    max_daily_cost_usd = Column(Float, nullable=True)
    max_monthly_cost_usd = Column(Float, nullable=True)
    max_cost_per_request_usd = Column(Float, nullable=True)
    max_tokens_per_request = Column(Integer, nullable=True)

    enforce_data_residency = Column(Boolean, default=False)
    data_residency_region = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    provider = relationship("AIProvider", back_populates="policies")
