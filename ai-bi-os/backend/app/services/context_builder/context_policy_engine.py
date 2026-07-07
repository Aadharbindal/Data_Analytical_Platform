from typing import Dict, Any, List
from app.schemas.context_builder import ContextPayload

class ContextPolicyEngine:
    def __init__(self, max_context_size: int = 128000, min_confidence: float = 0.6):
        self.max_context_size = max_context_size
        self.min_confidence = min_confidence

    def enforce_confidence_threshold(self, payload: ContextPayload) -> ContextPayload:
        # Filter analytics items that do not meet the minimum confidence
        valid_kpis = [k for k in payload.analytics_context.kpis if k.get("confidence", 1.0) >= self.min_confidence]
        valid_metrics = [m for m in payload.analytics_context.business_metrics if m.get("confidence", 1.0) >= self.min_confidence]
        
        payload.analytics_context.kpis = valid_kpis
        payload.analytics_context.business_metrics = valid_metrics
        
        return payload

    def check_workspace_isolation(self, user_workspace: str, target_workspace: str) -> bool:
        return user_workspace == target_workspace

    def apply_policies(self, payload: ContextPayload, user_workspace: str, target_workspace: str) -> ContextPayload:
        if not self.check_workspace_isolation(user_workspace, target_workspace):
            raise ValueError("Workspace isolation policy violation.")
            
        payload = self.enforce_confidence_threshold(payload)
        return payload
