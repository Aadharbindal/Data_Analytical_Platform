from typing import Dict, Any

class ExecutionValidator:
    def __init__(self):
        pass

    def validate(self, final_output: Dict[str, Any], validation_rules: Dict[str, Any]) -> bool:
        """
        Validates the output against the rules specified in the execution plan.
        """
        if not final_output:
            return False
            
        # MVP: assume valid if we got content back
        return "content" in final_output
