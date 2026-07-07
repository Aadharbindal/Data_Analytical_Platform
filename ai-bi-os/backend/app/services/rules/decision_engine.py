from sqlalchemy.orm import Session
from typing import List, Tuple, Dict, Any
from app.models.rule import BusinessRule, Decision
from app.models.insight import Insight

class DecisionEngine:
    """Generates Decision objects from triggered rules."""
    
    @staticmethod
    def generate_decisions(db: Session, triggered_results: List[Tuple[BusinessRule, Dict[str, Any]]], dataset_version_id: str) -> List[Decision]:
        decisions = []
        
        for rule, context in triggered_results:
            insight: Insight = context.get("insight")
            
            decision = Decision(
                dataset_version_id=dataset_version_id,
                rule_id=rule.id,
                insight_id=insight.id if insight else None,
                title=f"Action Required: {rule.name}",
                description=f"Rule '{rule.name}' triggered based on insight '{insight.title}'." if insight else "",
                priority=rule.priority,
                severity=rule.severity,
                business_domain=rule.business_domain,
                affected_entities=insight.affected_entities if insight else [],
                confidence=insight.score.confidence if insight and insight.score else 1.0
            )
            decisions.append(decision)
            
        return decisions
