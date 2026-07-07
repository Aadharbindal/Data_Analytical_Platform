from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Float, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class DatasetSchema(Base):
    __tablename__ = "dataset_schemas"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    version = relationship("DatasetVersion")
    columns = relationship("SchemaColumn", back_populates="schema", cascade="all, delete-orphan")
    quality = relationship("SchemaQuality", back_populates="schema", uselist=False, cascade="all, delete-orphan")
    fingerprint = relationship("SchemaFingerprint", back_populates="schema", uselist=False, cascade="all, delete-orphan")
    relationships = relationship("SchemaRelationship", back_populates="schema", cascade="all, delete-orphan")

class SchemaColumn(Base):
    __tablename__ = "schema_columns"
    id = Column(String, primary_key=True, default=generate_uuid)
    schema_id = Column(String, ForeignKey("dataset_schemas.id"))
    
    # Discovery
    position = Column(Integer, nullable=False)
    original_header = Column(String, nullable=False)
    normalized_header = Column(String, nullable=False)
    
    # Types & Semantics
    detected_data_type = Column(String, nullable=False)  # Pandas/Arrow type (e.g. object, int64)
    inferred_semantic_type = Column(String, nullable=True) # e.g. Email, Date, Currency
    business_meaning = Column(String, nullable=True)       # e.g. Customer ID
    classification = Column(String, nullable=True)         # Dimension, Measure, Timestamp, Identifier
    
    # Constraints & Keys
    is_nullable = Column(Boolean, default=True)
    is_unique = Column(Boolean, default=False)
    is_primary_key_candidate = Column(Boolean, default=False)
    is_foreign_key_candidate = Column(Boolean, default=False)
    is_required = Column(Boolean, default=False)
    default_value = Column(String, nullable=True)
    
    schema = relationship("DatasetSchema", back_populates="columns")

class SchemaQuality(Base):
    __tablename__ = "schema_quality"
    id = Column(String, primary_key=True, default=generate_uuid)
    schema_id = Column(String, ForeignKey("dataset_schemas.id"), unique=True)
    
    completeness_score = Column(Float, default=0.0)
    naming_quality_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    normalization_score = Column(Float, default=0.0)
    relationship_score = Column(Float, default=0.0)
    overall_quality_score = Column(Float, default=0.0)
    
    schema = relationship("DatasetSchema", back_populates="quality")

class SchemaFingerprint(Base):
    __tablename__ = "schema_fingerprints"
    id = Column(String, primary_key=True, default=generate_uuid)
    schema_id = Column(String, ForeignKey("dataset_schemas.id"), unique=True)
    
    dataset_signature = Column(String, nullable=False)
    schema_hash = Column(String, nullable=False)
    column_hash = Column(String, nullable=False)
    structure_hash = Column(String, nullable=False)
    
    schema = relationship("DatasetSchema", back_populates="fingerprint")

class SchemaRelationship(Base):
    __tablename__ = "schema_relationships"
    id = Column(String, primary_key=True, default=generate_uuid)
    schema_id = Column(String, ForeignKey("dataset_schemas.id"))
    
    source_column_id = Column(String, ForeignKey("schema_columns.id"))
    target_entity_name = Column(String, nullable=False) # e.g., 'customers'
    target_column_name = Column(String, nullable=False) # e.g., 'customer_id'
    confidence_score = Column(Float, default=0.0)
    
    schema = relationship("DatasetSchema", back_populates="relationships")
    source_column = relationship("SchemaColumn")
