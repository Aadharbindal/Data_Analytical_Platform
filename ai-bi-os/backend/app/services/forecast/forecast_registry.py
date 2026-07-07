import logging
from typing import List

logger = logging.getLogger("ForecastRegistry")

class ForecastRegistry:
    """Registers supported forecast methodologies."""
    
    def __init__(self):
        self.supported_models = [
            "NAIVE",
            "MOVING_AVERAGE",
            "WEIGHTED_MOVING_AVERAGE",
            "SIMPLE_EXPONENTIAL_SMOOTHING",
            "HOLT_WINTERS",
            "ARIMA",
            "SARIMA",
            "PROPHET"
        ]
        
    def get_supported_models(self) -> List[str]:
        return self.supported_models

forecast_registry = ForecastRegistry()
