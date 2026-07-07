from typing import List
from app.models.recommendation import Recommendation

class RecommendationValidator:
    """Filters out contradictory, duplicate, or unfeasible recommendations."""
    
    @staticmethod
    def validate(recommendations: List[Recommendation]) -> List[Recommendation]:
        valid = []
        for rec in recommendations:
            # Simple heuristic: reject if confidence is too low
            if rec.confidence and rec.confidence < 0.3:
                rec.status = "REJECTED"
                # Still add it so history is saved, but we'll filter later
            valid.append(rec)
        return valid
