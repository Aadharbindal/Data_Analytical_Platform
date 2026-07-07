import logging

logger = logging.getLogger("CorrelationValidator")

class CorrelationValidator:
    """
    Validates pairs for correlation (checks for constants, missing values).
    """
    
    def validate_pair(self, col_x_stats: dict, col_y_stats: dict, min_sample_size: int = 30) -> bool:
        """
        Rejects combinations that shouldn't be correlated.
        """
        # 1. Sample size
        n_x = col_x_stats.get("non_null_count", 0)
        n_y = col_y_stats.get("non_null_count", 0)
        # In reality we need pairwise non-null count, but this is a rough proxy
        if min(n_x, n_y) < min_sample_size:
            return False
            
        # 2. Constant columns (variance = 0 or distinct count = 1)
        if col_x_stats.get("distinct_count", 2) <= 1 or col_y_stats.get("distinct_count", 2) <= 1:
            return False
            
        return True

correlation_validator = CorrelationValidator()
