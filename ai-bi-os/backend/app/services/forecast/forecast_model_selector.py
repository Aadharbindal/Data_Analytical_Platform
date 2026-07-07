import logging
from typing import Dict, Any, List

logger = logging.getLogger("ForecastModelSelector")

class ForecastModelSelector:
    """Auto-evaluates models using AIC/BIC/RMSE."""
    
    def select_best_model(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mock selection: Returns the model with the lowest AIC/RMSE."""
        
        if not candidates:
            raise ValueError("No candidates provided for selection")
            
        best = min(candidates, key=lambda x: x.get("aic", float("inf")))
        return best

forecast_model_selector = ForecastModelSelector()
