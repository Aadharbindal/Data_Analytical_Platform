import logging
from typing import Dict, Any, List

logger = logging.getLogger("ForecastPlanner")

class ForecastPlanner:
    """Prepares scenario constraints (Baseline vs Optimistic)."""
    
    def generate_scenarios(self, base_predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Takes a base horizon and builds specific business bands."""
        
        opt_series = []
        con_series = []
        
        for p in base_predictions:
            ts = p["timestamp"]
            ev = p["expected_value"]
            opt_series.append({"timestamp": ts, "scenario_value": ev * 1.15}) # +15%
            con_series.append({"timestamp": ts, "scenario_value": ev * 0.85}) # -15%
            
        return [
            {
                "scenario_type": "OPTIMISTIC",
                "business_impact_score": 85.0,
                "scenario_series": opt_series
            },
            {
                "scenario_type": "CONSERVATIVE",
                "business_impact_score": 40.0,
                "scenario_series": con_series
            }
        ]

forecast_planner = ForecastPlanner()
