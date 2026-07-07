from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Float, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class QualityAssessment(Base):
    __tablename__ = "quality_assessments"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    version = relationship("DatasetVersion")
    dimensions = relationship("QualityDimension", back_populates="assessment", cascade="all, delete-orphan")
    violations = relationship("QualityViolation", back_populates="assessment", cascade="all, delete-orphan")
    score = relationship("QualityScore", back_populates="assessment", uselist=False, cascade="all, delete-orphan")

class QualityDimension(Base):
    """
    Stores scores for: Completeness, Consistency, Accuracy, Validity, 
    Uniqueness, Integrity, Timeliness, Conformity, Reliability, Readiness
    """
    __tablename__ = "quality_dimensions"
    id = Column(String, primary_key=True, default=generate_uuid)
    assessment_id = Column(String, ForeignKey("quality_assessments.id"))
    
    dimension_name = Column(String, nullable=False) # e.g. "Completeness"
    score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    explanation = Column(Text, nullable=True)
    improvement_suggestions = Column(JSON, nullable=True)
    
    assessment = relationship("QualityAssessment", back_populates="dimensions")

class QualityViolation(Base):
    __tablename__ = "quality_violations"
    id = Column(String, primary_key=True, default=generate_uuid)
    assessment_id = Column(String, ForeignKey("quality_assessments.id"))
    schema_column_id = Column(String, ForeignKey("schema_columns.id"), nullable=True)
    
    issue_category = Column(String, nullable=False) # e.g., "Missing Value", "Regex Mismatch"
    severity = Column(String, nullable=False) # "Critical", "High", "Medium", "Low"
    priority = Column(String, nullable=False) # "P1", "P2", "P3"
    
    affected_rows_count = Column(Integer, default=0)
    confidence = Column(Float, default=1.0)
    root_cause = Column(Text, nullable=True)
    suggested_fix = Column(Text, nullable=True)
    estimated_impact = Column(Text, nullable=True)
    
    assessment = relationship("QualityAssessment", back_populates="violations")
    schema_column = relationship("SchemaColumn")

class QualityScore(Base):
    __tablename__ = "quality_scores"
    id = Column(String, primary_key=True, default=generate_uuid)
    assessment_id = Column(String, ForeignKey("quality_assessments.id"), unique=True)
    
    overall_score = Column(Float, default=0.0)
    business_readiness_score = Column(Float, default=0.0)
    analytics_readiness_score = Column(Float, default=0.0)
    ai_readiness_score = Column(Float, default=0.0)
    
    assessment = relationship("QualityAssessment", back_populates="score")
