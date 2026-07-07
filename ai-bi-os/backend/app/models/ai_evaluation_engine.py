from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Text, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class EvaluationSuite(Base):
    """Represents a collection of benchmarks targeting a specific domain."""
    __tablename__ = "ai_eval_suites"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    target_module = Column(String, nullable=False) # e.g. SQL_AGENT, RECOMMENDATION_ENGINE

class BenchmarkDataset(Base):
    """Represents a golden dataset used in a suite."""
    __tablename__ = "ai_eval_benchmark_datasets"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    suite_id = Column(String, ForeignKey("ai_eval_suites.id", ondelete="CASCADE"))
    dataset_type = Column(String, nullable=False) # GOLDEN, SYNTHETIC, HISTORICAL
    storage_uri = Column(String, nullable=False)
    
    suite = relationship("EvaluationSuite")

class EvaluationObject(Base):
    """Core entity tracking a specific evaluation run."""
    __tablename__ = "ai_eval_objects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    suite_id = Column(String, ForeignKey("ai_eval_suites.id", ondelete="CASCADE"), nullable=True)
    
    evaluation_type = Column(String, nullable=False) # MODEL, PROMPT, WORKFLOW
    target_module = Column(String, nullable=False) 
    
    model_version = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    
    quality_score = Column(Float, nullable=False, default=0.0)
    cost_score = Column(Float, nullable=False, default=0.0)
    latency_score = Column(Float, nullable=False, default=0.0)
    overall_score = Column(Float, nullable=False, default=0.0)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    metrics = relationship("EvaluationMetric", back_populates="evaluation", cascade="all, delete-orphan")
    runs = relationship("EvaluationRun", back_populates="evaluation", cascade="all, delete-orphan")

class EvaluationMetric(Base):
    """Granular metrics for an evaluation object."""
    __tablename__ = "ai_eval_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    evaluation_id = Column(String, ForeignKey("ai_eval_objects.id", ondelete="CASCADE"))
    
    metric_name = Column(String, nullable=False) # Accuracy, Precision, Recall, F1, Groundedness, Latency, Cost
    metric_value = Column(Float, nullable=False)
    
    evaluation = relationship("EvaluationObject", back_populates="metrics")

class EvaluationRun(Base):
    """Individual item evaluations within a suite."""
    __tablename__ = "ai_eval_runs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    evaluation_id = Column(String, ForeignKey("ai_eval_objects.id", ondelete="CASCADE"))
    
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=False)
    expected_data = Column(JSON, nullable=True)
    
    is_success = Column(Boolean, nullable=False)
    latency_ms = Column(Integer, nullable=False)
    token_usage = Column(Integer, nullable=False)
    cost_usd = Column(Float, nullable=False)
    
    evaluation = relationship("EvaluationObject", back_populates="runs")

class Leaderboard(Base):
    """Materialized ranking of models/prompts/workflows."""
    __tablename__ = "ai_eval_leaderboards"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    category = Column(String, nullable=False) # MODEL, PROMPT, WORKFLOW
    
    entity_name = Column(String, nullable=False) # e.g. "gpt-4-turbo"
    overall_rank = Column(Integer, nullable=False)
    aggregated_score = Column(Float, nullable=False)
    
    last_updated = Column(DateTime, default=datetime.utcnow)

class RegressionReport(Base):
    """Alerts generated when performance drops."""
    __tablename__ = "ai_eval_regression_reports"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    evaluation_id = Column(String, ForeignKey("ai_eval_objects.id", ondelete="CASCADE"))
    
    metric_name = Column(String, nullable=False)
    previous_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    degradation_percentage = Column(Float, nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    evaluation = relationship("EvaluationObject")

class EvaluationHistory(Base):
    """Audit log of evaluations."""
    __tablename__ = "ai_eval_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    event = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class EvaluationAudit(Base):
    """Security audit log."""
    __tablename__ = "ai_eval_audit"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
