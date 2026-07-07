from sqlalchemy.orm import Session
import time
from app.models.rule import BusinessRule, RuleExecution
from app.models.insight import Insight
from app.services.rules.rule_executor import RuleExecutor
from app.services.rules.decision_engine import DecisionEngine

class RuleOrchestrator:
    """Coordinates the full execution of active rules against insights."""
    
    @staticmethod
    def process_rules(db: Session, dataset_version_id: str) -> int:
        try:
            # 1. Fetch active rules
            # We assume a single workspace for now, or we'd filter by workspace_id
            rules = db.query(BusinessRule).filter(BusinessRule.is_active == True).all()
            if not rules:
                return 0
                
            # 2. Fetch recent insights to act as context
            insights = db.query(Insight).filter(
                Insight.dataset_version_id == dataset_version_id,
                Insight.status == "VALIDATED"
            ).all()
            
            contexts = [{"insight": insight} for insight in insights]
            
            # 3. Execute
            start_time = time.perf_counter()
            triggered = RuleExecutor.execute(rules, contexts)
            end_time = time.perf_counter()
            
            # Log Executions
            for rule in rules:
                evaluated_true = any(r.id == rule.id for r, _ in triggered)
                execution = RuleExecution(
                    rule_id=rule.id,
                    dataset_version_id=dataset_version_id,
                    status="SUCCESS",
                    evaluated_true=evaluated_true,
                    execution_time_ms=(end_time - start_time) * 1000
                )
                db.add(execution)
            
            # 4. Generate Decisions
            if triggered:
                decisions = DecisionEngine.generate_decisions(db, triggered, dataset_version_id)
                db.add_all(decisions)
                
            db.commit()
            return len(triggered)
            
        except Exception as e:
            db.rollback()
            raise e
