from typing import Dict, Any, List
from app.schemas.evidence import EvidencePayload, EvidenceReferenceBase

class EvidenceBuilder:
    def __init__(self):
        pass

    def build_evidence_payload(self, extracted_data: Dict[str, Any], plan: Dict[str, Any]) -> EvidencePayload:
        """
        Builds the detailed EvidencePayload.
        """
        payload = EvidencePayload(
            analytical_method_used="Determinstic Context Extraction"
        )
        
        if plan.get("extract_kpi") and extracted_data.get("kpis"):
            payload.supporting_metrics = extracted_data["kpis"]
            
        if plan.get("extract_statistical") and extracted_data.get("eda"):
            payload.supporting_statistics = [extracted_data["eda"]]
            
        if plan.get("extract_forecast") and extracted_data.get("forecasts"):
            payload.supporting_objects = [extracted_data["forecasts"]]
            
        return payload

    def map_references(self, context_id: str) -> List[EvidenceReferenceBase]:
        refs = [
            EvidenceReferenceBase(source_type="CONTEXT_OBJECT", source_id=context_id)
        ]
        return refs
