from sqlalchemy.orm import Session
from typing import Dict, Any, Tuple
from app.services.context_builder import ContextBuilderService
from app.schemas.context_builder import ContextObjectResponse

class EvidenceExtractor:
    def __init__(self, db: Session):
        self.db = db
        self.context_service = ContextBuilderService(db)

    def extract_from_context(self, context_id: str) -> Tuple[ContextObjectResponse, Dict[str, Any]]:
        """
        Extracts raw objects from ContextBuilder.
        """
        context_obj = self.context_service.get_context(context_id)
        if not context_obj:
            raise ValueError(f"Context Object {context_id} not found.")

        extracted_data = {
            "kpis": context_obj.context_payload.analytics_context.kpis,
            "eda": context_obj.context_payload.analytics_context.eda_summary,
            "forecasts": context_obj.context_payload.analytics_context.forecast_summary
        }
        
        return context_obj, extracted_data
