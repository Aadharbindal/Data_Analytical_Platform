import logging
from typing import List

logger = logging.getLogger("ValidationRegistry")

class ValidationRegistry:
    """Registers types of targets supported for validation."""
    
    def __init__(self):
        self.supported_targets = [
            "KPI",
            "BUSINESS_METRIC",
            "EDA",
            "CORRELATION",
            "STATISTICS",
            "REGRESSION",
            "FORECASTING"
        ]
        
    def is_supported(self, target_type: str) -> bool:
        return target_type.upper() in self.supported_targets

validation_registry = ValidationRegistry()
