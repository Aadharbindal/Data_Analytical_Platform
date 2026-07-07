import logging
from typing import Dict, Any, List

from app.services.outlier.threshold_engine import threshold_engine

logger = logging.getLogger("OutlierDetector")

class OutlierDetector:
    """Core detection logic (IQR, MAD, Z-score)."""
    
    def detect_outliers(self, col_stats: Dict[str, Any], raw_values: List[float], method: str = "IQR") -> List[Dict[str, Any]]:
        """Mock detection returning a list of outliers found in the provided mock array."""
        
        lower, upper = threshold_engine.calculate_bounds(method, col_stats)
        mean = col_stats.get("mean", 0.0)
        median = col_stats.get("median", 0.0)
        
        outliers = []
        for i, val in enumerate(raw_values):
            if val < lower or val > upper:
                outliers.append({
                    "row_reference": f"row_{i}",
                    "actual_value": val,
                    "detection_method": method,
                    "outlier_type": "GLOBAL",
                    "distance_from_mean": abs(val - mean),
                    "distance_from_median": abs(val - median)
                })
                
        return outliers

outlier_detector = OutlierDetector()
