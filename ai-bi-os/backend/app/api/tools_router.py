from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.tools import (
    ToolRegistrationRequest, ToolResponse,
    ToolExecutionRequest, ToolExecutionResponse,
    ToolValidationRequest
)
from app.services.tool_engine import ToolEngineService

router = APIRouter(prefix="/tools", tags=["Tool Calling Engine"])

@router.post("/register", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
def register_tool(request: ToolRegistrationRequest, db: Session = Depends(get_db)):
    service = ToolEngineService(db)
    return service.register_tool(request)

@router.get("", response_model=List[ToolResponse])
def get_tools(db: Session = Depends(get_db)):
    service = ToolEngineService(db)
    return service.get_all_tools()

@router.get("/{tool_id}", response_model=ToolResponse)
def get_tool(tool_id: str, db: Session = Depends(get_db)):
    service = ToolEngineService(db)
    try:
        return service.get_tool(tool_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/execute", response_model=ToolExecutionResponse)
def execute_tool(request: ToolExecutionRequest, db: Session = Depends(get_db)):
    service = ToolEngineService(db)
    try:
        return service.execute_tool(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/validate")
def validate_tool(request: ToolValidationRequest, db: Session = Depends(get_db)):
    service = ToolEngineService(db)
    try:
        service.validate_tool_call(request)
        return {"status": "Valid"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/executions/history", response_model=List[ToolExecutionResponse])
def get_history(db: Session = Depends(get_db)):
    service = ToolEngineService(db)
    return service.get_executions()

@router.post("/cancel")
def cancel_execution(execution_id: str, db: Session = Depends(get_db)):
    service = ToolEngineService(db)
    try:
        service.cancel_execution(execution_id)
        return {"status": "Cancelled"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
