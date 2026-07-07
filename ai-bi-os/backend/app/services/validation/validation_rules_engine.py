import logging
from typing import Dict, Any, List

logger = logging.getLogger("ValidationRulesEngine")

class ValidationRulesEngine:
    """
    Verifies assessed metrics against expected bounds (Rules).
    """
    
    def evaluate_rules(self, metrics: Dict[str, float], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        
        for rule in rules:
            metric_val = metrics.get(rule["metric_name"])
            if metric_val is None:
                continue
                
            passed = False
            op = rule["operator"]
            thresh = rule["threshold_value"]
            
            if op == "GREATER_THAN":
                passed = metric_val > thresh
            elif op == "LESS_THAN":
                passed = metric_val < thresh
            elif op == "EQUALS":
                passed = metric_val == thresh
                
            results.append({
                "rule_id": rule.get("id", "default"),
                "metric_name": rule["metric_name"],
                "passed": passed,
                "is_critical": rule.get("is_critical", True),
                "actual_value": metric_val
            })
            
        return results

validation_rules_engine = ValidationRulesEngine()
