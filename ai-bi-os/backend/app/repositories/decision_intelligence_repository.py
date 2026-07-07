from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any

from app.models.decision_intelligence import (
    DecisionObject, DecisionReference, DecisionScenario, DecisionComparison,
    DecisionPolicy, DecisionApproval, DecisionHistory, DecisionMetrics
)

class DecisionIntelligenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_decision(self, decision: DecisionObject) -> DecisionObject:
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)
        return decision

    def get_decision(self, decision_id: str) -> Optional[DecisionObject]:
        return self.db.query(DecisionObject).filter(DecisionObject.id == decision_id).first()

    def update_decision(self, decision: DecisionObject) -> DecisionObject:
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)
        return decision

    def list_decisions(self, workspace_id: str, limit: int = 50) -> List[DecisionObject]:
        return self.db.query(DecisionObject).filter(
            DecisionObject.workspace_id == workspace_id
        ).order_by(DecisionObject.business_priority.asc(), DecisionObject.generated_at.desc()).limit(limit).all()

    def add_reference(self, reference: DecisionReference):
        self.db.add(reference)
        self.db.commit()

    def add_scenario(self, scenario: DecisionScenario):
        self.db.add(scenario)
        self.db.commit()

    def add_comparison(self, comparison: DecisionComparison):
        self.db.add(comparison)
        self.db.commit()
        
    def add_policy(self, policy: DecisionPolicy):
        self.db.add(policy)
        self.db.commit()
        
    def add_approval(self, approval: DecisionApproval):
        self.db.add(approval)
        self.db.commit()

    def add_history(self, history: DecisionHistory):
        self.db.add(history)
        self.db.commit()

    def log_metrics(self, metric: DecisionMetrics):
        self.db.add(metric)
        self.db.commit()
