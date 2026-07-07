from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.sql_agent import (
    SQLQueryRequest, SQLQueryResponse,
    SQLValidationRequest, SQLExecutionRequest, SQLExecutionResponse,
    SchemaMetadataResponse, BusinessGlossaryEntry
)
from app.services.sql_agent import SQLAgentService

router = APIRouter(prefix="/sql", tags=["SQL Analytics Agent"])

@router.post("/query", response_model=SQLQueryResponse, status_code=status.HTTP_201_CREATED)
def generate_sql_query(request: SQLQueryRequest, db: Session = Depends(get_db)):
    service = SQLAgentService(db)
    try:
        return service.generate_query(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/validate")
def validate_sql(request: SQLValidationRequest, db: Session = Depends(get_db)):
    service = SQLAgentService(db)
    try:
        service.validate_sql(request)
        return {"status": "Valid", "message": "SQL is safe to execute."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/explain")
def explain_sql(request: SQLValidationRequest, db: Session = Depends(get_db)):
    # Re-use validate for now, in a full implementation this would run EXPLAIN ANALYZE
    service = SQLAgentService(db)
    try:
        service.validate_sql(request)
        return {"status": "Explained", "plan": "Sequential Scan"} # Mock
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/execute", response_model=SQLExecutionResponse)
def execute_sql(request: SQLExecutionRequest, db: Session = Depends(get_db)):
    service = SQLAgentService(db)
    try:
        return service.execute_query(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history", response_model=List[SQLQueryResponse])
def get_query_history(db: Session = Depends(get_db)):
    service = SQLAgentService(db)
    return service.get_history()

@router.get("/schema", response_model=List[SchemaMetadataResponse])
def get_schema_metadata(workspace_id: str, db: Session = Depends(get_db)):
    service = SQLAgentService(db)
    return service.get_schema(workspace_id)

@router.get("/glossary", response_model=List[BusinessGlossaryEntry])
def get_business_glossary(workspace_id: str, db: Session = Depends(get_db)):
    service = SQLAgentService(db)
    return service.get_glossary(workspace_id)
