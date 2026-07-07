from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, Text, DateTime
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class AnalyticsRun(Base):
    """Tracks the overarching execution of the analytics job for a dataset version."""
    __tablename__ = "analytics_runs"
    id = Column(String, primary_key=True, default=generate_uuid)
    
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"), nullable=False)
    status = Column(String, default="RUNNING") # RUNNING, COMPLETED, FAILED
    
    execution_time_ms = Column(Float, default=0.0)
    metrics_generated = Column(Integer, default=0)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

class AnalyticsBusinessMetric(Base):
    """Stores calculated KPIs (Revenue, GMV, etc.) at a specific aggregation level."""
    __tablename__ = "analytics_business_metrics"
    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("analytics_runs.id"))
    
    metric_name = Column(String, nullable=False) # e.g., "Revenue", "Profit"
    value = Column(Float, nullable=False)
    
    aggregation_level = Column(String, default="GLOBAL")
    dimension = Column(String, nullable=True)
    dimension_value = Column(String, nullable=True)

class TrendAnalysis(Base):
    """Stores detected trends (Increasing, Decreasing, Stable)."""
    __tablename__ = "analytics_trends"
    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("analytics_runs.id"))
    
    metric_name = Column(String, nullable=False)
    time_dimension = Column(String, nullable=False)
    
    trend_direction = Column(String, nullable=False) # INCREASING, DECREASING, STABLE
    slope = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    seasonality_detected = Column(Boolean, default=False)

class SegmentAnalysis(Base):
    """Stores metrics sliced by dimensional categories."""
    __tablename__ = "analytics_segments"
    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("analytics_runs.id"))
    
    dimension = Column(String, nullable=False)
    segment_value = Column(String, nullable=False)
    
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    percentage_of_total = Column(Float, nullable=True)

class VarianceAnalysis(Base):
    """Stores period-over-period variances."""
    __tablename__ = "analytics_variances"
    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("analytics_runs.id"))
    
    metric_name = Column(String, nullable=False)
    current_period_value = Column(Float, nullable=False)
    previous_period_value = Column(Float, nullable=False)
    
    absolute_variance = Column(Float, nullable=False)
    percentage_variance = Column(Float, nullable=False)

class CorrelationAnalysis(Base):
    """Stores statistical correlation matrices."""
    __tablename__ = "analytics_correlations"
    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("analytics_runs.id"))
    
    column_x = Column(String, nullable=False)
    column_y = Column(String, nullable=False)
    
    correlation_coefficient = Column(Float, nullable=False) # e.g. Pearson r
    method = Column(String, default="PEARSON")
    significance_p_value = Column(Float, nullable=True)

class InsightObject(Base):
    """A structured JSON representation of an insight."""
    __tablename__ = "analytics_insights"
    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("analytics_runs.id"))
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False) # structured text, no LLM fluff
    metric = Column(String, nullable=False)
    
    evidence_data = Column(JSON, nullable=False) # e.g., actual values backing the insight
    calculation_method = Column(String, nullable=False)
    
    confidence = Column(Float, nullable=True)
    severity = Column(String, nullable=True) # HIGH, MEDIUM, LOW
    
    affected_dimensions = Column(JSON, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
