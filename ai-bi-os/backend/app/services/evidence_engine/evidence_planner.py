from typing import Dict, Any
from app.schemas.evidence import EvidenceBuildRequest

class EvidencePlanner:
    def __init__(self):
        pass

    def plan_extraction(self, request: EvidenceBuildRequest) -> Dict[str, Any]:
        """
        Plans how to extract data from the ContextObject.
        For MVP, we extract all KPIs and EDA from Context.
        """
        plan = {
            "extract_statistical": True,
            "extract_forecast": True,
            "extract_kpi": True,
            "required_confidence": 0.6
        }
        return plan
