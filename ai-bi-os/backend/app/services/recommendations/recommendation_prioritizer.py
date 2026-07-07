from typing import List
from app.models.recommendation import Recommendation

class RecommendationPrioritizer:
    """Ranks recommendations by ROI, Impact, and Urgency."""
    
    @staticmethod
    def prioritize(recommendations: List[Recommendation]) -> None:
        valid_recs = [r for r in recommendations if r.status != "REJECTED"]
        
        for rec in valid_recs:
            score = rec.score
            if not score:
                continue
                
            roi_score = min(rec.roi_estimate / 10000.0, 1.0) if rec.roi_estimate else 0.1
            score.roi_score = roi_score
            score.business_value_score = 0.8 if rec.priority in ["CRITICAL", "HIGH"] else 0.4
            score.feasibility_score = 0.9 if rec.implementation_effort != "HIGH" else 0.4
            
            # Weighted sum
            final = (roi_score * 0.4) + (score.urgency_score * 0.3) + (score.business_value_score * 0.2) + (score.feasibility_score * 0.1)
            score.final_score = final
            
        # Optional: could sort them, but we usually sort on read via SQL
