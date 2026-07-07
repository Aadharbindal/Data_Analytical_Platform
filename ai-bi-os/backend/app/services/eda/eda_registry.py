import logging
from typing import List, Dict

logger = logging.getLogger("EDARegistry")

class EDARegistry:
    """
    Registers the available statistical functions and analyses that the EDA Engine can perform.
    This allows dynamic expansion of analytical capabilities later.
    """
    
    def __init__(self):
        self._analyzers = {
            "numeric": ["count", "sum", "mean", "median", "mode", "min", "max", "variance", 
                        "std_dev", "cv", "skewness", "kurtosis", "iqr"],
            "categorical": ["frequency_dist", "top_k", "bottom_k", "entropy", "rare"],
            "date": ["min_date", "max_date", "time_span", "seasonality_check", "granularity"],
            "text": ["avg_len", "max_len", "min_len", "vocab_size", "language", "common_tokens"],
            "boolean": ["true_count", "false_count", "true_ratio"]
        }
        
    def get_analyzers_for_type(self, data_type: str) -> List[str]:
        # simplified mapping
        if data_type.upper() in ["INTEGER", "FLOAT", "DOUBLE", "NUMERIC", "DECIMAL"]:
            return self._analyzers["numeric"]
        elif data_type.upper() in ["VARCHAR", "TEXT", "STRING"]:
            return self._analyzers["text"] + self._analyzers["categorical"]
        elif data_type.upper() in ["DATE", "TIMESTAMP", "DATETIME"]:
            return self._analyzers["date"]
        elif data_type.upper() in ["BOOLEAN", "BOOL"]:
            return self._analyzers["boolean"]
        return []

eda_registry = EDARegistry()
