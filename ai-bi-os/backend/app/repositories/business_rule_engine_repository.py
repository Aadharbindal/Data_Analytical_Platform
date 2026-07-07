from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any

from app.models.business_rule_engine import (
    RuleDefinition, BusinessRuleEngineVersion, BusinessRuleEngineExecution, RuleGroup,
    RulePolicy, BusinessRuleEngineAudit, RuleMetrics
)

class BusinessRuleEngineRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_rule(self, rule: RuleDefinition) -> RuleDefinition:
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_rule(self, rule_id: str) -> Optional[RuleDefinition]:
        return self.db.query(RuleDefinition).filter(RuleDefinition.id == rule_id).first()

    def update_rule(self, rule: RuleDefinition) -> RuleDefinition:
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def list_rules(self, workspace_id: str, limit: int = 100) -> List[RuleDefinition]:
        return self.db.query(RuleDefinition).filter(
            RuleDefinition.workspace_id == workspace_id
        ).order_by(RuleDefinition.priority.asc(), RuleDefinition.created_at.desc()).limit(limit).all()

    def get_active_rules(self, workspace_id: str) -> List[RuleDefinition]:
        return self.db.query(RuleDefinition).filter(
            RuleDefinition.workspace_id == workspace_id,
            RuleDefinition.status == "ACTIVE"
        ).order_by(RuleDefinition.priority.asc()).all()

    def add_execution(self, execution: BusinessRuleEngineExecution):
        self.db.add(execution)
        self.db.commit()
        
    def add_version(self, version: BusinessRuleEngineVersion):
        self.db.add(version)
        self.db.commit()

    def log_metrics(self, metric: RuleMetrics):
        self.db.add(metric)
        self.db.commit()
