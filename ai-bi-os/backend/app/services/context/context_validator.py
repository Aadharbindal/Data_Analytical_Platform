from typing import List
from app.models.context import ContextItem, ContextValidation

class ContextValidator:
    """Rejects invalid evidence or conflicting items."""
    
    @staticmethod
    def validate(items: List[ContextItem]) -> List[ContextItem]:
        valid_items = []
        for item in items:
            is_valid = True
            reason = None
            
            # Example heuristic: reject very low confidence insights
            if item.source_type == "INSIGHT" and item.content.get("confidence", 1.0) < 0.2:
                is_valid = False
                reason = "Low confidence insight."
                
            item.validation = ContextValidation(
                is_valid=is_valid,
                rejection_reason=reason
            )
            
            if is_valid:
                valid_items.append(item)
                
        return valid_items
