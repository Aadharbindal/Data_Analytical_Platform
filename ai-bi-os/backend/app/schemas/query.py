from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    sql: str
    dataset_version_id: str
    workspace_id: str
    skip_cache: bool = False

class QueryMetadata(BaseModel):
    cache_hit: bool
    execution_time_ms: float
    rows_returned: int

class QueryResponse(BaseModel):
    schema_: List[Dict[str, str]] # e.g., [{"name": "col_a", "type": "VARCHAR"}]
    rows: List[Dict[str, Any]]
    metadata: QueryMetadata
    
    class Config:
        populate_by_name = True
        alias_generator = lambda string: 'schema' if string == 'schema_' else string

class QueryExplainResponse(BaseModel):
    logical_plan: str

class QueryHistoryResponse(BaseModel):
    id: str
    query_sql: str
    status: str
    execution_time_ms: float
    rows_returned: int
    cache_hit: bool
    error_message: Optional[str]
    executed_at: Any
    
    class Config:
        from_attributes = True
