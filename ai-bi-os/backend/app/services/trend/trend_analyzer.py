import logging
from typing import Dict, Any

logger = logging.getLogger("TrendAnalyzer")

class TrendAnalyzer:
    """Overall trajectory and momentum scoring."""
    
    def generate_profile(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates overarching trend based on metadata."""
        
        start = metadata.get("start_val", 0.0)
        end = metadata.get("end_val", 0.0)
        
        overall = "STABLE"
        if end > start * 1.05:
            overall = "INCREASING"
        elif end < start * 0.95:
            overall = "DECREASING"
            
        return {
            "overall_trend": overall,
            "signal_to_noise_ratio": metadata.get("signal_to_noise_ratio", 2.5),
            "trend_stability": metadata.get("trend_stability", 85.0)
        }

trend_analyzer = TrendAnalyzer()
