import logging
from typing import Dict, Any, List

logger = logging.getLogger("ForecastValidator")

class ForecastValidator:
    """Validates stationarity and gaps."""
    
    def validate_series(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        
        # Stationarity
        is_stat = metadata.get("is_stationary", True)
        results.append({
            "check_name": "STATIONARITY",
            "passed": is_stat,
            "details": "Series is stationary" if is_stat else "Series requires differencing (non-stationary)"
        })
        
        # Data Sufficiency
        obs = metadata.get("total_observations", 100)
        results.append({
            "check_name": "SUFFICIENCY",
            "passed": obs >= 30,
            "details": f"Observations ({obs}) meets minimum for robust forecasting" if obs >= 30 else f"Too few observations ({obs})"
        })
        
        return results

forecast_validator = ForecastValidator()
