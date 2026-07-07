from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, Text, DateTime
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class QueryHistory(Base):
    """Tracks every query executed by the engine."""
    __tablename__ = "query_history"
    id = Column(String, primary_key=True, default=generate_uuid)
    
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=True)
    
    query_sql = Column(Text, nullable=False)
    status = Column(String, nullable=False) # "SUCCESS", "FAILED"
    
    execution_time_ms = Column(Float, default=0.0)
    rows_scanned = Column(Integer, default=0)
    rows_returned = Column(Integer, default=0)
    
    cache_hit = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    
    executed_at = Column(DateTime, default=datetime.utcnow)

class QueryCache(Base):
    """Stores query results to avoid re-execution."""
    __tablename__ = "query_cache"
    id = Column(String, primary_key=True, default=generate_uuid)
    
    query_hash = Column(String, unique=True, index=True, nullable=False)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"), nullable=True)
    
    result_data = Column(JSON, nullable=True) # Could also be a path to a cached parquet file for large results
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class MaterializedView(Base):
    """Tracks pre-computed aggregations."""
    __tablename__ = "materialized_views"
    id = Column(String, primary_key=True, default=generate_uuid)
    
    view_name = Column(String, unique=True, nullable=False)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    
    definition_sql = Column(Text, nullable=False)
    
    last_refreshed_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    status = Column(String, default="ACTIVE") # "ACTIVE", "STALE", "REFRESHING"
