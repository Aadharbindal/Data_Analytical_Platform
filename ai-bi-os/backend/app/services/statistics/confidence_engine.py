import logging
from typing import Dict, Any, List

logger = logging.getLogger("ConfidenceEngine")

class ConfidenceEngine:
    """Calculates confidence intervals and margin of error."""
    
    def calculate_intervals(self, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for m in metrics:
            if m["type"] != "NUMERIC": continue
            
            mean = m.get("stats", {}).get("mean", 100)
            std_err = m.get("stats", {}).get("std_dev", 10) / (100 ** 0.5)
            moe = 1.96 * std_err # 95% CI Z-score
            
            results.append({
                "metric_name": m["name"],
                "confidence_level": 0.95,
                "mean_estimate": mean,
                "margin_of_error": moe,
                "lower_bound": mean - moe,
                "upper_bound": mean + moe
            })
            
        return results

confidence_engine = ConfidenceEngine()
