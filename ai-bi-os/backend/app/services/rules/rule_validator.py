from sqlalchemy.orm import Session
from app.models.rule import BusinessRule, RuleDependency

class RuleValidator:
    """Checks for circular dependencies, unreachable conditions, etc."""
    
    @staticmethod
    def validate_dependencies(db: Session, new_rule_id: str, trigger_rule_id: str) -> bool:
        """Prevent A -> B -> A loops."""
        visited = set()
        
        def check_cycle(current_id: str):
            if current_id in visited:
                return True
            visited.add(current_id)
            deps = db.query(RuleDependency).filter(RuleDependency.parent_rule_id == current_id).all()
            for d in deps:
                if d.child_rule_id == new_rule_id or check_cycle(d.child_rule_id):
                    return True
            return False
            
        return not check_cycle(trigger_rule_id)
