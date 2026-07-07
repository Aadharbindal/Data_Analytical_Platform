from typing import Dict, Any
from app.schemas.prompt import PromptBuildRequest

class PromptPlanner:
    def __init__(self):
        pass

    def plan(self, request: PromptBuildRequest) -> Dict[str, Any]:
        """
        Determines what sections should be included in the prompt.
        """
        plan = {
            "include_system": True,
            "include_business": True,
            "include_dataset": False,
            "include_analytics": True,
            "include_evidence": True,
            "include_constraints": True
        }
        
        if request.prompt_type == "SQLPrompt":
            plan["include_dataset"] = True
            
        return plan
