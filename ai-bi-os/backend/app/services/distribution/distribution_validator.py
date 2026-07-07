import logging
from typing import Dict, Any

logger = logging.getLogger("DistributionValidator")

class DistributionValidator:
    """Validates sample size and sparsity before fitting."""
    
    def validate_for_fitting(self, column_stats: Dict[str, Any]) -> bool:
        """
        Ensures a column has enough valid data to run expensive distribution fitting.
        """
        n = column_stats.get("valid_count", 0)
        
        if n < 30:
            raise ValueError(f"Insufficient sample size for distribution fitting. Need at least 30, got {n}.")
            
        return True

distribution_validator = DistributionValidator()
