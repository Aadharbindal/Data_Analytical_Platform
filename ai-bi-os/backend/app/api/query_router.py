from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.query.query_orchestrator import QueryOrchestrator
from app.services.query.query_validator import QueryValidator
from app.models.query import QueryHistory, QueryCache
from app.schemas.query import QueryRequest, QueryResponse, QueryExplainResponse, QueryHistoryResponse

router = APIRouter(prefix="/api/v1/query", tags=["query"])

@router.post("/execute", response_model=QueryResponse)
def execute_query(req: QueryRequest, db: Session = Depends(get_db)):
    """Executes a Read-Only SQL Analytical Query using DuckDB."""
    # Convert 'schema_' internal name back to 'schema' for the external output
    # (Pydantic handles this via alias, but we just pass the raw dict)
    res = QueryOrchestrator.execute_query(
        db, req.sql, req.dataset_version_id, req.workspace_id, req.skip_cache
    )
    return res

@router.post("/explain", response_model=QueryExplainResponse)
def explain_query(req: QueryRequest, db: Session = Depends(get_db)):
    """Returns the DuckDB execution plan without running the query."""
    plan = QueryOrchestrator.explain_query(db, req.sql, req.dataset_version_id)
    return {"logical_plan": plan}

@router.post("/validate")
def validate_query(req: QueryRequest):
    """Checks SQL for forbidden keywords."""
    QueryValidator.validate(req.sql)
    return {"status": "valid"}

@router.get("/history", response_model=List[QueryHistoryResponse])
def get_query_history(workspace_id: str, db: Session = Depends(get_db)):
    history = db.query(QueryHistory).filter(QueryHistory.workspace_id == workspace_id).order_by(QueryHistory.executed_at.desc()).limit(100).all()
    return history

@router.delete("/cache")
def clear_cache(db: Session = Depends(get_db)):
    db.query(QueryCache).delete()
    db.commit()
    return {"status": "cache cleared"}
