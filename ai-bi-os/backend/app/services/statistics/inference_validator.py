import logging
from typing import Dict, Any

logger = logging.getLogger("InferenceValidator")

class InferenceValidator:
    """
    Validates data against statistical assumptions (normality, variance).
    """
    
    def check_normality(self, data_stats: Dict[str, Any]) -> bool:
        """
        Mock check based on skewness/kurtosis (in prod, uses Shapiro-Wilk from stats models).
        """
        skew = data_stats.get("skewness", 0)
        kurt = data_stats.get("kurtosis", 3)
        return abs(skew) < 0.5 and 2.5 < kurt < 3.5
        
    def check_equal_variance(self, group_a_stats: Dict[str, Any], group_b_stats: Dict[str, Any]) -> bool:
        """
        Mock Levene's test for equal variance.
        """
        var_a = group_a_stats.get("variance", 1)
        var_b = group_b_stats.get("variance", 1)
        # Roughly equal if ratio is < 2
        return max(var_a, var_b) / min(var_a, var_b) < 2.0

inference_validator = InferenceValidator()
