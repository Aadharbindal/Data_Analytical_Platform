from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

class BusinessGlossaryEntry(BaseModel):
    workspace_id: str
    term: str
    description: Optional[str] = None
    mapped_schema: Optional[str] = None
    mapped_table: str
    mapped_column: Optional[str] = None

class SchemaMetadataResponse(BaseModel):
    workspace_id: str
    schema_name: str
    table_name: str
    columns: List[Dict[str, str]]
    primary_keys: Optional[List[str]] = None
    foreign_keys: Optional[List[Dict[str, str]]] = None

class SQLQueryRequest(BaseModel):
    workspace_id: str
    user_request: str
    context_data: Optional[Dict[str, Any]] = None # Passed from orchestrator
    dialect: str = "duckdb"

class SQLQueryResponse(BaseModel):
    query_id: str
    user_request: str
    detected_intent: Optional[str] = None
    generated_sql: str
    dialect: str
    is_validated: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SQLValidationRequest(BaseModel):
    query_id: str
    generated_sql: str

class SQLExecutionRequest(BaseModel):
    query_id: str
    use_cache: bool = True

class SQLExecutionResponse(BaseModel):
    execution_id: str
    query_id: str
    generated_sql: str
    status: str
    rows_returned: int
    execution_time_ms: Optional[int] = None
    data: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None
    model_config = ConfigDict(from_attributes=True)
