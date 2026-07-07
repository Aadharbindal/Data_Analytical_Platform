from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, Text, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class MetadataCatalog(Base):
    """The central hub for a dataset's unified metadata."""
    __tablename__ = "metadata_catalogs"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("datasets.id"), unique=True)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"))
    
    last_indexed_at = Column(DateTime, default=datetime.utcnow)
    
    dataset = relationship("Dataset")
    version = relationship("DatasetVersion")
    
    tags = relationship("DatasetTag", back_populates="catalog", cascade="all, delete-orphan")
    entries = relationship("CatalogEntry", back_populates="catalog", cascade="all, delete-orphan")
    documentation = relationship("DatasetDocumentation", back_populates="catalog", uselist=False, cascade="all, delete-orphan")
    score = relationship("CatalogScore", back_populates="catalog", uselist=False, cascade="all, delete-orphan")
    recommendations = relationship("CatalogRecommendation", back_populates="catalog", cascade="all, delete-orphan")

class CatalogEntry(Base):
    """Key-value pairs for technical metadata (e.g. row count, file size)."""
    __tablename__ = "catalog_entries"
    id = Column(String, primary_key=True, default=generate_uuid)
    catalog_id = Column(String, ForeignKey("metadata_catalogs.id"))
    
    category = Column(String, nullable=False) # e.g. "Schema", "Profile", "Privacy"
    key = Column(String, nullable=False)
    value = Column(JSON, nullable=False)
    
    catalog = relationship("MetadataCatalog", back_populates="entries")

class DatasetTag(Base):
    """Tags applied to the dataset."""
    __tablename__ = "dataset_tags"
    id = Column(String, primary_key=True, default=generate_uuid)
    catalog_id = Column(String, ForeignKey("metadata_catalogs.id"))
    
    tag_name = Column(String, nullable=False)
    tag_type = Column(String, default="Auto") # "Manual", "Auto", "Governance"
    
    catalog = relationship("MetadataCatalog", back_populates="tags")

class BusinessGlossaryEntry(Base):
    """Global glossary aggregated across datasets."""
    __tablename__ = "global_business_glossary"
    id = Column(String, primary_key=True, default=generate_uuid)
    
    term = Column(String, unique=True, nullable=False)
    definition = Column(Text, nullable=False)
    aliases = Column(JSON, default=list)
    related_datasets = Column(JSON, default=list)

class CatalogSearchIndex(Base):
    """Highly normalized table for extremely fast ranked SQL searches."""
    __tablename__ = "catalog_search_index"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("datasets.id"))
    
    token = Column(String, nullable=False, index=True) # The actual searchable word (lowercase)
    token_type = Column(String, nullable=False) # e.g. "DatasetName", "Tag", "SemanticEntity", "Column"
    weight = Column(Integer, default=1) # Ranking weight
    
    dataset = relationship("Dataset")

class DatasetDocumentation(Base):
    """Auto-generated markdown summaries."""
    __tablename__ = "dataset_documentation"
    id = Column(String, primary_key=True, default=generate_uuid)
    catalog_id = Column(String, ForeignKey("metadata_catalogs.id"), unique=True)
    
    business_summary = Column(Text, nullable=False)
    technical_summary = Column(Text, nullable=False)
    recommended_kpis = Column(JSON, default=list)
    
    catalog = relationship("MetadataCatalog", back_populates="documentation")

class CatalogRecommendation(Base):
    """Recommended datasets or joins."""
    __tablename__ = "catalog_recommendations"
    id = Column(String, primary_key=True, default=generate_uuid)
    catalog_id = Column(String, ForeignKey("metadata_catalogs.id"))
    
    recommendation_type = Column(String, nullable=False) # "Related Dataset", "Join Candidate"
    target_dataset_id = Column(String, nullable=True)
    reasoning = Column(String, nullable=False)
    
    catalog = relationship("MetadataCatalog", back_populates="recommendations")

class CatalogScore(Base):
    """Rolled up scores for sorting/filtering."""
    __tablename__ = "catalog_scores"
    id = Column(String, primary_key=True, default=generate_uuid)
    catalog_id = Column(String, ForeignKey("metadata_catalogs.id"), unique=True)
    
    popularity_score = Column(Float, default=0.0) # Usage based
    freshness_score = Column(Float, default=100.0)
    quality_score = Column(Float, default=0.0)
    trust_score = Column(Float, default=0.0) # Aggregate of privacy + quality
    ai_readiness_score = Column(Float, default=0.0) # How well semanticly mapped it is
    
    catalog = relationship("MetadataCatalog", back_populates="score")
