from typing import Dict, Any

class ExecutionMonitor:
    def __init__(self):
        pass

    def check_timeout(self, started_at, timeout_ms: int) -> bool:
        """
        In production, this would monitor running executions and kill them if they exceed timeout_ms.
        """
        # MVP stub
        return False
