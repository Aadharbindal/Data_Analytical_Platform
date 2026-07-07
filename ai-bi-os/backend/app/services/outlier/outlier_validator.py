import logging
from typing import Dict, Any

logger = logging.getLogger("OutlierValidator")

class OutlierValidator:
    """Validates low sample sizes, missing data, etc."""
    
    def validate_for_detection(self, column_stats: Dict[str, Any]) -> bool:
        """
        Ensures a column has enough valid data to run outlier detection.
        """
        n = column_stats.get("valid_count", 0)
        
        if n < 10:
            raise ValueError(f"Insufficient sample size for outlier detection. Need at least 10, got {n}.")
            
        return True

outlier_validator = OutlierValidator()
