import logging
from typing import List

logger = logging.getLogger("OutlierRegistry")

class OutlierRegistry:
    """Registers supported outlier detection methodologies."""
    
    def __init__(self):
        self.supported_methods = [
            "IQR",
            "Z_SCORE",
            "MODIFIED_Z_SCORE",
            "PERCENTILE",
            "MAD",
            "TUKEY",
            "EVT"
        ]
        
    def is_supported(self, method_name: str) -> bool:
        return method_name.upper() in self.supported_methods
        
    def get_supported_methods(self) -> List[str]:
        return self.supported_methods

outlier_registry = OutlierRegistry()
