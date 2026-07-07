from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.rule import BusinessRule, RuleCondition, Decision
from app.models.dataset import DatasetVersion
from app.schemas.rule import BusinessRuleSchema, BusinessRuleCreate, DecisionSchema

router = APIRouter(prefix="/api/v1/rules", tags=["rules"])

@router.post("", response_model=BusinessRuleSchema)
def create_rule(rule_in: BusinessRuleCreate, db: Session = Depends(get_db)):
    """Create a new deterministic business rule."""
    new_rule = BusinessRule(
        workspace_id=rule_in.workspace_id,
        name=rule_in.name,
        description=rule_in.description,
        business_domain=rule_in.business_domain,
        priority=rule_in.priority,
        severity=rule_in.severity
    )
    db.add(new_rule)
    db.flush()
    
    condition = RuleCondition(
        rule_id=new_rule.id,
        ast=rule_in.condition.ast
    )
    db.add(condition)
    db.commit()
    db.refresh(new_rule)
    
    return new_rule

@router.get("", response_model=List[BusinessRuleSchema])
def list_rules(workspace_id: str, db: Session = Depends(get_db)):
    """List all active rules for a workspace."""
    rules = db.query(BusinessRule).filter(
        BusinessRule.workspace_id == workspace_id,
        BusinessRule.is_active == True
    ).all()
    return rules

@router.post("/execute")
def trigger_rule_execution(dataset_version_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually triggers rule execution against a dataset's insights."""
    from app.worker import process_rule_task
    
    version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Dataset version not found")
         
    process_rule_task.delay(dataset_version_id=dataset_version_id)
    return {"status": "accepted", "message": "Rule execution queued"}

@router.get("/decisions", response_model=List[DecisionSchema])
def get_decisions(dataset_version_id: str, db: Session = Depends(get_db)):
    """Gets generated decisions for a dataset."""
    decisions = db.query(Decision).filter(
        Decision.dataset_version_id == dataset_version_id
    ).all()
    return decisions
