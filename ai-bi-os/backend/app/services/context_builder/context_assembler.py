from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.schemas.context_builder import ContextBuildRequest, ContextPayload, AnalyticsContext
from app.services.analytics_registry_service import AnalyticsRegistryService
from app.schemas.analytics_registry import ObjectSearchRequest

class ContextAssembler:
    def __init__(self, db: Session):
        self.db = db
        self.analytics_registry = AnalyticsRegistryService(db)

    def assemble(self, request: ContextBuildRequest, plan: Dict[str, Any]) -> tuple[ContextPayload, List[Dict[str, Any]]]:
        """
        Assembles the payload from Analytics Objects.
        Returns (payload, list_of_references).
        """
        payload = ContextPayload()
        references = []
        
        # Base query criteria
        search_criteria = ObjectSearchRequest(
            workspace_id=request.workspace_id,
            dataset_id=request.dataset_id,
            limit=50
        )
        
        # 1. Fetch KPIs
        if plan.get("fetch_kpis"):
            search_criteria.object_type = "KPI"
            kpis, _ = self.analytics_registry.search_objects(search_criteria)
            for k in kpis:
                payload.analytics_context.kpis.append(k.payload)
                references.append({"id": k.id, "relevance_score": 1.0})
                payload.analytics_context.confidence_scores[k.id] = k.confidence_score or 1.0

        # 2. Fetch EDA/Trends
        if plan.get("fetch_eda"):
            search_criteria.object_type = "EDA"
            eda_objs, _ = self.analytics_registry.search_objects(search_criteria)
            if eda_objs:
                payload.analytics_context.eda_summary = eda_objs[0].payload
                references.append({"id": eda_objs[0].id, "relevance_score": 0.9})
                payload.analytics_context.confidence_scores[eda_objs[0].id] = eda_objs[0].confidence_score or 1.0

        # 3. Fetch Forecasts
        if plan.get("fetch_forecast"):
            search_criteria.object_type = "FORECAST"
            forecasts, _ = self.analytics_registry.search_objects(search_criteria)
            if forecasts:
                payload.analytics_context.forecast_summary = forecasts[0].payload
                references.append({"id": forecasts[0].id, "relevance_score": 0.95})
                payload.analytics_context.confidence_scores[forecasts[0].id] = forecasts[0].confidence_score or 1.0

        return payload, references
