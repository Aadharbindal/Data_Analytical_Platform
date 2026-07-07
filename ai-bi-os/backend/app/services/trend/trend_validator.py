import logging
from typing import Dict, Any, List

logger = logging.getLogger("TrendValidator")

class TrendValidator:
    """Validates minimum windows and SNR constraints."""
    
    def validate_trend_signal(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock check returning validation results based on metadata flags."""
        
        results = []
        
        # Min Window
        n = metadata.get("total_observations", 0)
        results.append({
            "check_name": "MIN_WINDOW",
            "passed": n >= 10,
            "details": f"Total observations ({n}) meets minimum window size of 10" if n >= 10 else f"Too few observations ({n})"
        })
        
        # Noise Level
        snr = metadata.get("signal_to_noise_ratio", 2.0)
        results.append({
            "check_name": "NOISE_LEVEL",
            "passed": snr >= 1.5,
            "details": f"SNR ({snr}) is acceptable" if snr >= 1.5 else f"Signal is too noisy (SNR: {snr})"
        })
        
        return results

trend_validator = TrendValidator()
