from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Float, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class TransformationPipeline(Base):
    """A saved, ordered sequence of transformation steps."""
    __tablename__ = "transformation_pipelines"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("datasets.id"))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    steps = relationship("TransformationStep", back_populates="pipeline", order_by="TransformationStep.step_order", cascade="all, delete-orphan")
    dataset = relationship("Dataset")

class TransformationStep(Base):
    """An individual atomic transformation operation (e.g. TRIM_WHITESPACE)."""
    __tablename__ = "transformation_steps"
    id = Column(String, primary_key=True, default=generate_uuid)
    pipeline_id = Column(String, ForeignKey("transformation_pipelines.id"))
    
    step_order = Column(Integer, nullable=False)
    operation_type = Column(String, nullable=False) # e.g. "DROP_COLUMN", "FILL_NULLS"
    target_column = Column(String, nullable=True)   # Can be null for row-level operations
    parameters = Column(JSON, nullable=False, default=dict) # {"strategy": "mean"}
    
    pipeline = relationship("TransformationPipeline", back_populates="steps")

class CleaningRecommendation(Base):
    """System-generated suggestion on how to fix a QualityViolation."""
    __tablename__ = "cleaning_recommendations"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"))
    quality_violation_id = Column(String, ForeignKey("quality_violations.id"), nullable=True)
    
    recommended_operation = Column(String, nullable=False)
    target_column = Column(String, nullable=True)
    recommended_parameters = Column(JSON, default=dict)
    confidence_score = Column(Float, default=0.0)
    reasoning = Column(Text, nullable=True)
    
    version = relationship("DatasetVersion")

class CleaningHistory(Base):
    """Immutable audit log of pipeline execution and dataset version bumping."""
    __tablename__ = "cleaning_history"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("datasets.id"))
    
    original_version_id = Column(String, ForeignKey("dataset_versions.id"))
    new_version_id = Column(String, ForeignKey("dataset_versions.id"))
    pipeline_id = Column(String, ForeignKey("transformation_pipelines.id"), nullable=True)
    
    executed_at = Column(DateTime, default=datetime.utcnow)
    execution_time_ms = Column(Integer, nullable=True)
    affected_rows = Column(Integer, nullable=True)
    
    # We store a snapshot of steps here in case the pipeline is edited later.
    snapshot_steps = Column(JSON, nullable=False)
    
    dataset = relationship("Dataset")
    original_version = relationship("DatasetVersion", foreign_keys=[original_version_id])
    new_version = relationship("DatasetVersion", foreign_keys=[new_version_id])
