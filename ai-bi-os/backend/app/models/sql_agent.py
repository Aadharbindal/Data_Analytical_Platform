from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, Text, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class BusinessGlossary(Base):
    """Maps natural language business terms to database entities."""
    __tablename__ = "sql_business_glossary"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    
    term = Column(String, nullable=False) # e.g. "Revenue"
    description = Column(String, nullable=True)
    
    mapped_schema = Column(String, nullable=True)
    mapped_table = Column(String, nullable=False)
    mapped_column = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SchemaMetadata(Base):
    """Automatically discovered metadata for safe SQL generation."""
    __tablename__ = "sql_schema_metadata"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    
    schema_name = Column(String, nullable=True, default="public")
    table_name = Column(String, nullable=False)
    
    columns = Column(JSON, nullable=False) # List of column names and types
    primary_keys = Column(JSON, nullable=True)
    foreign_keys = Column(JSON, nullable=True)
    
    last_scanned = Column(DateTime, default=datetime.utcnow)

class SQLQuery(Base):
    """The core record of a generated query."""
    __tablename__ = "sql_queries"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    
    user_request = Column(Text, nullable=False)
    detected_intent = Column(String, nullable=True)
    
    generated_sql = Column(Text, nullable=False)
    dialect = Column(String, nullable=False, default="duckdb") # duckdb, postgres, snowflake, etc.
    
    is_validated = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    executions = relationship("SQLExecution", back_populates="query", cascade="all, delete-orphan")
    validations = relationship("SQLValidation", back_populates="query", cascade="all, delete-orphan")

class SQLValidation(Base):
    """Records of queries rejected or modified for safety."""
    __tablename__ = "sql_validations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    query_id = Column(String, ForeignKey("sql_queries.id", ondelete="CASCADE"))
    
    is_safe = Column(Boolean, nullable=False)
    rejection_reason = Column(String, nullable=True) # e.g. "Contains DROP statement"
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    query = relationship("SQLQuery", back_populates="validations")

class SQLExecution(Base):
    """The runtime instance of a query against a DB."""
    __tablename__ = "sql_executions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    query_id = Column(String, ForeignKey("sql_queries.id", ondelete="CASCADE"))
    
    status = Column(String, nullable=False, default="PENDING") # PENDING, RUNNING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    query = relationship("SQLQuery", back_populates="executions")
    metrics = relationship("SQLMetrics", uselist=False, back_populates="execution", cascade="all, delete-orphan")
    history = relationship("SQLHistory", back_populates="execution", cascade="all, delete-orphan")

class SQLHistory(Base):
    """Immutable log of SQL agent activity."""
    __tablename__ = "sql_execution_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    execution_id = Column(String, ForeignKey("sql_executions.id", ondelete="CASCADE"))
    
    status_to = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    execution = relationship("SQLExecution", back_populates="history")

class SQLMetrics(Base):
    """Performance, row counts, and latency."""
    __tablename__ = "sql_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    execution_id = Column(String, ForeignKey("sql_executions.id", ondelete="CASCADE"), unique=True)
    
    execution_time_ms = Column(Integer, nullable=True)
    rows_returned = Column(Integer, default=0)
    
    execution = relationship("SQLExecution", back_populates="metrics")

class SqlAgentQueryCache(Base):
    """Storing deterministic results for identical queries."""
    __tablename__ = "sql_query_cache"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, nullable=False, index=True)
    
    query_hash = Column(String, nullable=False, index=True) # Hash of the SQL string
    result_payload = Column(JSON, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
