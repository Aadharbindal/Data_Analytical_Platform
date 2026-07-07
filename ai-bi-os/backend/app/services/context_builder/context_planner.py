from typing import List, Dict, Any
from app.schemas.context_builder import ContextBuildRequest

class ContextPlanner:
    def __init__(self):
        pass

    def plan_context(self, request: ContextBuildRequest) -> Dict[str, Any]:
        """
        Determines the intent and the types of analytics objects needed.
        """
        plan = {
            "fetch_kpis": True,
            "fetch_metrics": True,
            "fetch_eda": False,
            "fetch_forecast": False,
            "intent": "general_exploration"
        }
        
        if request.question:
            q_lower = request.question.lower()
            if "forecast" in q_lower or "predict" in q_lower or "future" in q_lower:
                plan["fetch_forecast"] = True
                plan["intent"] = "forecasting"
            if "trend" in q_lower or "history" in q_lower:
                plan["fetch_eda"] = True
                plan["intent"] = "trend_analysis"
                
        return plan
