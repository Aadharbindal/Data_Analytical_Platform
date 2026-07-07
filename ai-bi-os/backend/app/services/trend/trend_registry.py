import logging
from typing import List

logger = logging.getLogger("TrendRegistry")

class TrendRegistry:
    """Registers supported trend and change point methodologies."""
    
    def __init__(self):
        self.supported_change_methods = [
            "CUSUM",
            "VARIANCE_SHIFT",
            "ROLLING_MEAN_SHIFT",
            "BAYESIAN_CP"
        ]
        
    def is_method_supported(self, method_name: str) -> bool:
        return method_name.upper() in self.supported_change_methods

trend_registry = TrendRegistry()
