from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.business_rule_engine import (
    RuleCreateRequest,
    RuleEvaluateRequest,
    RuleResponse,
    RuleExecutionResponse,
    RuleListResponse
)
from app.services.business_rule_engine.rule_engine_service import RuleEngineService

router = APIRouter(prefix="/business-rules-engine", tags=["business-rule-engine"])

@router.post("/create", response_model=RuleResponse)
def create_rule(request: RuleCreateRequest, db: Session = Depends(get_db)):
    service = RuleEngineService(db)
    try:
        rule = service.create_rule(request)
        return rule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate", response_model=List[RuleExecutionResponse])
def evaluate_rules(request: RuleEvaluateRequest, db: Session = Depends(get_db)):
    service = RuleEngineService(db)
    executions = service.evaluate(request)
    return executions

@router.get("/workspace/{workspace_id}", response_model=RuleListResponse)
def get_rules_by_workspace(workspace_id: str, db: Session = Depends(get_db)):
    service = RuleEngineService(db)
    rules = service.list_by_workspace(workspace_id)
    return RuleListResponse(rules=rules, total=len(rules))

@router.get("/{rule_id}", response_model=RuleResponse)
def get_rule(rule_id: str, db: Session = Depends(get_db)):
    service = RuleEngineService(db)
    rule = service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule
