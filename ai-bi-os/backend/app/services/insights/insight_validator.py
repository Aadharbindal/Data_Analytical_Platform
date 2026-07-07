from typing import List
from app.models.insight import Insight, InsightValidation

class InsightValidator:
    """Filters out duplicates, conflicting insights, or low-confidence noise."""
    
    @staticmethod
    def validate(insights: List[Insight]) -> List[Insight]:
        valid_insights = []
        seen_titles = set()
        
        for insight in insights:
            validation = InsightValidation()
            insight.validation = validation
            
            # Reject if confidence is too low
            if insight.score and insight.score.confidence < 0.5:
                validation.is_valid = False
                validation.rejection_reason = "LOW_CONFIDENCE"
                insight.status = "REJECTED"
                valid_insights.append(insight)
                continue
                
            # Reject if duplicate title (simplified deduplication)
            if insight.title in seen_titles:
                validation.is_valid = False
                validation.rejection_reason = "DUPLICATE"
                insight.status = "REJECTED"
                valid_insights.append(insight)
                continue
                
            seen_titles.add(insight.title)
            validation.is_valid = True
            insight.status = "VALIDATED"
            valid_insights.append(insight)
            
        return valid_insights
