import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger("ValidationPolicyEngine")

class ValidationPolicyEngine:
    """Aggregates rule results to enforce strict policies."""
    
    def enforce_policy(self, rule_results: List[Dict[str, Any]]) -> Tuple[str, List[str], List[str]]:
        """
        Determines overall status: APPROVED, REJECTED, WARNING.
        Returns status, errors, warnings.
        """
        status = "APPROVED"
        errors = []
        warnings = []
        
        for res in rule_results:
            if not res["passed"]:
                msg = f"Failed rule on {res['metric_name']} (Value: {res['actual_value']})"
                if res["is_critical"]:
                    status = "REJECTED"
                    errors.append(msg)
                else:
                    if status != "REJECTED":
                        status = "WARNING"
                    warnings.append(msg)
                    
        return status, errors, warnings

validation_policy_engine = ValidationPolicyEngine()
