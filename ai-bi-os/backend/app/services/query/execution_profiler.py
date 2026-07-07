import time
import contextlib
from typing import Dict, Any

class ExecutionProfiler:
    """Wraps query execution to capture performance metrics."""
    
    @contextlib.contextmanager
    def profile(self):
        start_time = time.perf_counter()
        
        # Yield a dict that the caller can populate with row counts
        stats = {"rows_returned": 0, "rows_scanned": 0}
        try:
            yield stats
        finally:
            end_time = time.perf_counter()
            stats["execution_time_ms"] = (end_time - start_time) * 1000
