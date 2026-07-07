from typing import Dict, Any
from app.schemas.tools import ToolExecutionResponse
from app.models.tools import ToolExecution

class ResponseNormalizer:
    def __init__(self):
        pass

    def normalize(self, execution: ToolExecution) -> ToolExecutionResponse:
        """
        Normalizes any tool's output into a standard ToolExecutionResponse structure.
        """
        return ToolExecutionResponse(
            execution_id=execution.id,
            tool_id=execution.tool_id,
            status=execution.status,
            output=execution.output,
            error_details=execution.error_details,
            latency_ms=execution.metrics.latency_ms if execution.metrics else None,
            started_at=execution.started_at,
            completed_at=execution.completed_at
        )
