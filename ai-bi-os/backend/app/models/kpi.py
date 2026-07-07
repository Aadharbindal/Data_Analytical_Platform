from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class KPIDefinition(Base):
    """Core definition of a business KPI."""
    __tablename__ = "kpi_definitions"
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False)
    
    name = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=False) # e.g., Revenue, Finance, Custom
    description = Column(String, nullable=True)
    
    is_custom = Column(Boolean, default=False)
    
    versions = relationship("KPIVersion", back_populates="definition", cascade="all, delete-orphan")
    calculations = relationship("KPICalculation", back_populates="definition")
    history = relationship("KPIHistory", back_populates="definition")

class KPIVersion(Base):
    """Tracks changes to the formula logic over time."""
    __tablename__ = "kpi_versions"
    id = Column(String, primary_key=True, default=generate_uuid)
    definition_id = Column(String, ForeignKey("kpi_definitions.id"))
    
    version_number = Column(Integer, nullable=False)
    author = Column(String, nullable=True)
    status = Column(String, default="ACTIVE") # DRAFT, ACTIVE, DEPRECATED
    
    formula_expression = Column(String, nullable=False) # e.g., (SUM(revenue) - SUM(cost)) / SUM(revenue)
    dependencies = Column(JSON, nullable=True) # list of KPI IDs this formula depends on
    
    activation_date = Column(DateTime, default=datetime.utcnow)
    
    definition = relationship("KPIDefinition", back_populates="versions")

class KPICalculation(Base):
    """The materialized result of a KPI executed against a specific dataset and slice."""
    __tablename__ = "kpi_calculations"
    id = Column(String, primary_key=True, default=generate_uuid)
    definition_id = Column(String, ForeignKey("kpi_definitions.id"))
    dataset_version_id = Column(String, nullable=False)
    
    dimension = Column(String, nullable=True) # e.g., 'Region'
    dimension_value = Column(String, nullable=True) # e.g., 'North America'
    time_window = Column(String, nullable=True) # e.g., 'Monthly'
    
    value = Column(Float, nullable=False)
    previous_value = Column(Float, nullable=True) # for MoM/YoY comparisons
    
    confidence_score = Column(Float, nullable=True)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    definition = relationship("KPIDefinition", back_populates="calculations")

class KPICache(Base):
    """Tracks cached KPI results to avoid re-running DuckDB queries."""
    __tablename__ = "kpi_caches"
    id = Column(String, primary_key=True, default=generate_uuid)
    cache_key = Column(String, unique=True, index=True, nullable=False)
    calculation_id = Column(String, ForeignKey("kpi_calculations.id"))
    
    expires_at = Column(DateTime, nullable=False)
    is_valid = Column(Boolean, default=True)

class KPIExecution(Base):
    """Observability log for KPI engine runs."""
    __tablename__ = "kpi_executions"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, nullable=False)
    
    execution_time_ms = Column(Float, nullable=False)
    cache_hits = Column(Integer, default=0)
    errors = Column(JSON, nullable=True)
    
    status = Column(String, default="SUCCESS")
    timestamp = Column(DateTime, default=datetime.utcnow)

class KPIHistory(Base):
    """Audit trail of KPI definition changes."""
    __tablename__ = "kpi_history"
    id = Column(String, primary_key=True, default=generate_uuid)
    definition_id = Column(String, ForeignKey("kpi_definitions.id"))
    
    action = Column(String, nullable=False) # CREATED, UPDATED, DEPRECATED
    author = Column(String, nullable=True)
    changes = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    definition = relationship("KPIDefinition", back_populates="history")
