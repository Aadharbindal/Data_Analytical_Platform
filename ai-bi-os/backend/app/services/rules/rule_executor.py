from typing import List, Dict, Any, Tuple
from app.models.rule import BusinessRule
from app.services.rules.rule_compiler import RuleCompiler

class RuleExecutor:
    """Safely runs compiled rules against contexts."""
    
    @staticmethod
    def execute(rules: List[BusinessRule], contexts: List[Dict[str, Any]]) -> List[Tuple[BusinessRule, Dict[str, Any]]]:
        """
        Executes a list of rules against a list of contexts (e.g. Insights).
        Returns a list of tuples (TriggeredRule, MatchingContext).
        """
        triggered = []
        
        for rule in rules:
            if not rule.condition or not rule.condition.ast:
                continue
                
            compiled_func = RuleCompiler.compile(rule.condition.ast)
            
            for context in contexts:
                try:
                    if compiled_func(context):
                        triggered.append((rule, context))
                except Exception:
                    # Log execution failure
                    pass
                    
        return triggered
