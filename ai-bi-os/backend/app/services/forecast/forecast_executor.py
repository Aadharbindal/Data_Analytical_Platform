import logging
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger("ForecastExecutor")

class ForecastExecutor:
    """Mock execution of models to yield predictions."""
    
    def execute_horizon(self, model_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a mock prediction array based on horizon lengths."""
        
        horizon = model_meta.get("horizon_period", "NEXT_MONTH")
        periods = 30 if horizon == "NEXT_MONTH" else 7
        
        start = datetime.utcnow()
        series = []
        base_val = model_meta.get("last_known_value", 100.0)
        
        for i in range(periods):
            ts = (start + timedelta(days=i)).isoformat()
            series.append({
                "timestamp": ts,
                "expected_value": base_val + (i * 0.5),
                "lower_bound": base_val + (i * 0.5) - 5.0,
                "upper_bound": base_val + (i * 0.5) + 5.0
            })
            
        return {
            "horizon_period": horizon,
            "forecast_type": model_meta.get("forecast_type", "CUSTOM"),
            "prediction_series": series,
            "confidence_level": 95.0
        }

forecast_executor = ForecastExecutor()
