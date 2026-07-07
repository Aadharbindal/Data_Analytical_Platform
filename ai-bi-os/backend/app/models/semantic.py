from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class SemanticDomain(Base):
    """The inferred industry domain (Retail, Finance, etc)"""
    __tablename__ = "semantic_domains"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"), unique=True)
    
    primary_domain = Column(String, nullable=False)
    confidence_score = Column(Float, default=0.0)
    matched_rules = Column(JSON, default=list)
    
    version = relationship("DatasetVersion")

class BusinessEntity(Base):
    """Core entities like Customer, Product, Order"""
    __tablename__ = "business_entities"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"))
    
    entity_name = Column(String, nullable=False) # e.g. "Customer"
    confidence_score = Column(Float, default=0.0)
    
    columns = relationship("SemanticColumn", back_populates="business_entity")

class SemanticMetric(Base):
    """KPIs like Revenue, GMV, MRR inferred from semantics"""
    __tablename__ = "semantic_metrics"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"))
    
    metric_name = Column(String, nullable=False) # e.g. "Revenue"
    calculation_type = Column(String, nullable=True) # e.g. "SUM", "AVG"
    confidence_score = Column(Float, default=0.0)
    
    columns = relationship("SemanticColumn", back_populates="semantic_metric")

class SemanticColumn(Base):
    """The mapping of a physical column to a business concept"""
    __tablename__ = "semantic_columns"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"))
    schema_column_id = Column(String, ForeignKey("schema_columns.id"))
    business_entity_id = Column(String, ForeignKey("business_entities.id"), nullable=True)
    semantic_metric_id = Column(String, ForeignKey("semantic_metrics.id"), nullable=True)
    
    column_type = Column(String, nullable=False) # "Dimension", "Fact", "Lookup", "ID"
    business_name = Column(String, nullable=False) # Resolved via Alias Engine
    confidence_score = Column(Float, default=0.0)
    is_primary_key = Column(Boolean, default=False)
    
    business_entity = relationship("BusinessEntity", back_populates="columns")
    semantic_metric = relationship("SemanticMetric", back_populates="columns")
    
class SemanticBusinessGlossary(Base):
    """Auto-generated business definitions"""
    __tablename__ = "business_glossary"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"))
    
    term = Column(String, nullable=False)
    definition = Column(String, nullable=False)
    aliases = Column(JSON, default=list)
    examples = Column(JSON, default=list)

class OntologyNode(Base):
    """A node in the Knowledge Graph ontology"""
    __tablename__ = "ontology_nodes"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"))
    
    node_label = Column(String, nullable=False) # e.g. "Customer"
    node_type = Column(String, nullable=False) # "Entity", "Event"
    
class OntologyEdge(Base):
    """An edge connecting two ontology nodes"""
    __tablename__ = "ontology_edges"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"))
    
    source_node_id = Column(String, ForeignKey("ontology_nodes.id"))
    target_node_id = Column(String, ForeignKey("ontology_nodes.id"))
    relation_name = Column(String, nullable=False) # e.g. "Places", "Contains"

class SemanticRecommendation(Base):
    """Analytics possibilities based on the semantic inference"""
    __tablename__ = "semantic_recommendations"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"))
    
    recommendation_text = Column(String, nullable=False)
    capability = Column(String, nullable=False) # "Forecasting", "Churn Analysis", "Segmentation"
