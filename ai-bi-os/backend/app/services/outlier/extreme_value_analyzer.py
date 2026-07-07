import logging
from typing import Dict, Any, List

logger = logging.getLogger("ExtremeValueAnalyzer")

class ExtremeValueAnalyzer:
    """Differentiates standard outliers from extreme tail values (EVT)."""
    
    def extract_extreme_values(self, col_stats: Dict[str, Any], raw_values: List[float]) -> List[Dict[str, Any]]:
        """Mock Extreme Value extraction based on 99.9th / 0.1st percentiles."""
        
        p99_9 = col_stats.get("p99_9", 999.0)
        p00_1 = col_stats.get("p00_1", -999.0)
        
        extremes = []
        for val in raw_values:
            if val > p99_9:
                extremes.append({
                    "extreme_type": "EXTREME_HIGH",
                    "value": val,
                    "tail_probability": 0.001
                })
            elif val < p00_1:
                extremes.append({
                    "extreme_type": "EXTREME_LOW",
                    "value": val,
                    "tail_probability": 0.001
                })
                
        return extremes

extreme_value_analyzer = ExtremeValueAnalyzer()
