from typing import Dict, Any
import json
from app.schemas.context_builder import ContextPayload

class ContextOptimizer:
    def __init__(self, max_size_bytes: int = 500000):
        self.max_size_bytes = max_size_bytes

    def optimize(self, payload: ContextPayload) -> ContextPayload:
        # 1. Remove duplicate KPIs (by title or ID)
        seen_kpis = set()
        unique_kpis = []
        for kpi in payload.analytics_context.kpis:
            title = kpi.get("title", "")
            if title not in seen_kpis:
                seen_kpis.add(title)
                unique_kpis.append(kpi)
        payload.analytics_context.kpis = unique_kpis

        # 2. Compress metadata (remove verbose tracing from summaries if present)
        if payload.analytics_context.eda_summary:
            payload.analytics_context.eda_summary.pop("verbose_logs", None)
            
        # 3. Size check and truncate if necessary
        payload_size = len(payload.model_dump_json().encode('utf-8'))
        if payload_size > self.max_size_bytes:
            # Truncate some less important stuff if it gets too big
            payload.analytics_context.kpis = payload.analytics_context.kpis[:10]
            
        return payload
