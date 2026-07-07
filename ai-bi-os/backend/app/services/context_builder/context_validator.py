from typing import Dict, Any, List
from app.schemas.context_builder import ContextValidationResponse, ContextObjectResponse

class ContextValidator:
    def __init__(self):
        pass

    def validate_context(self, context_obj: ContextObjectResponse) -> ContextValidationResponse:
        """
        Validates a completed context object for missing objects, broken references, etc.
        """
        response = ContextValidationResponse(is_valid=True)
        
        if not context_obj.context_payload.analytics_context.kpis and \
           not context_obj.context_payload.analytics_context.eda_summary:
            response.missing_objects.append("Primary Analytics (KPIs or EDA)")
            response.is_valid = False
            
        for ref in context_obj.references:
            if ref.relevance_score and ref.relevance_score < 0.4:
                response.low_confidence_objects.append(ref.analytics_object_id)
                
        return response
