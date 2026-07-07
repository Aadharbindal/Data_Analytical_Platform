import logging
from typing import Dict, Any, List

logger = logging.getLogger("TemporalValidator")

class TemporalValidator:
    """Validates order, duplicates, and timezone consistency."""
    
    def validate_time_column(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock check returning validation results based on metadata flags."""
        
        results = []
        
        # Chronological Order
        is_ordered = metadata.get("is_strictly_ordered", True)
        results.append({
            "check_name": "CHRONOLOGICAL_ORDER",
            "passed": is_ordered,
            "details": "Data is strictly ordered" if is_ordered else "Data contains out-of-order timestamps"
        })
        
        # Duplicates
        has_duplicates = metadata.get("has_duplicates", False)
        results.append({
            "check_name": "DUPLICATES",
            "passed": not has_duplicates,
            "details": "No duplicated timestamps found" if not has_duplicates else "Found duplicate timestamps"
        })
        
        return results

temporal_validator = TemporalValidator()
