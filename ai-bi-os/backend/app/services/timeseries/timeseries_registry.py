import logging
from typing import List

logger = logging.getLogger("TimeSeriesRegistry")

class TimeSeriesRegistry:
    """Registers supported temporal frequencies and window types."""
    
    def __init__(self):
        self.supported_frequencies = [
            "HOURLY", "DAILY", "WEEKLY", "MONTHLY", "QUARTERLY", "YEARLY", "MIXED"
        ]
        self.supported_windows = [
            "ROLLING_MEAN", "ROLLING_MEDIAN", "ROLLING_SUM", "ROLLING_MIN", 
            "ROLLING_MAX", "EXPANDING_SUM", "EXPANDING_MEAN"
        ]
        
    def is_frequency_supported(self, freq: str) -> bool:
        return freq.upper() in self.supported_frequencies

timeseries_registry = TimeSeriesRegistry()
