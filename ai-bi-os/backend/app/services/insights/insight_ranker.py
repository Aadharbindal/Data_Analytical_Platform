from typing import List
from app.models.insight import Insight, InsightRanking

class InsightRanker:
    """Assigns scores and ranks based on business impact and statistical significance."""
    
    @staticmethod
    def rank(insights: List[Insight]) -> List[Insight]:
        # Filter to only valid insights
        valid_insights = [i for i in insights if i.status == "VALIDATED"]
        
        for insight in valid_insights:
            score = insight.score
            if not score:
                continue
                
            # Basic ranking heuristic combining impact, confidence, and urgency
            # Weighting: Impact (40%), Confidence (40%), Urgency (20%)
            final_score = (score.business_impact * 0.4) + (score.confidence * 0.4) + (score.urgency * 0.2)
            
            ranking = InsightRanking(
                final_score=final_score
            )
            insight.ranking = ranking
            
        # Sort insights by final score descending
        valid_insights.sort(key=lambda x: x.ranking.final_score if x.ranking else 0, reverse=True)
        
        # Assign rank position
        for idx, insight in enumerate(valid_insights):
            if insight.ranking:
                insight.ranking.rank_position = idx + 1
                
        return insights # Return all insights, including rejected ones (for history), but valid ones are ranked
