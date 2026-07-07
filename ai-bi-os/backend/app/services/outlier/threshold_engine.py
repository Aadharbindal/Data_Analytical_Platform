import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("ThresholdEngine")

class ThresholdEngine:
    """Manages static, dynamic, and rule-based thresholds."""
    
    def calculate_bounds(self, method: str, col_stats: Dict[str, Any]) -> Tuple[float, float]:
        """
        Dynamically extracts upper/lower bounds based on the specified method.
        """
        if method == "IQR":
            q1 = col_stats.get("q1", 0.0)
            q3 = col_stats.get("q3", 0.0)
            iqr = q3 - q1
            multiplier = col_stats.get("multiplier", 1.5)
            
            lower = q1 - (multiplier * iqr)
            upper = q3 + (multiplier * iqr)
            return lower, upper
            
        elif method == "Z_SCORE":
            mean = col_stats.get("mean", 0.0)
            std = col_stats.get("std_dev", 1.0)
            multiplier = col_stats.get("multiplier", 3.0)
            
            lower = mean - (multiplier * std)
            upper = mean + (multiplier * std)
            return lower, upper
            
        # Default fallback (Percentile)
        return col_stats.get("p01", 0.0), col_stats.get("p99", 0.0)

threshold_engine = ThresholdEngine()
