from typing import List, Dict, Any
from app.models.context import ContextItem, ContextRanking, ContextSelection

class ContextRanker:
    """Deterministically scores relevance using keyword matching."""
    
    @staticmethod
    def rank(items: List[ContextItem], plan: Dict[str, Any]) -> None:
        keywords = plan.get("keywords", [])
        
        for item in items:
            content_str = str(item.content).lower()
            
            # 1. Semantic/Keyword Score
            match_count = sum(1 for kw in keywords if kw in content_str)
            semantic_score = match_count / len(keywords) if keywords else 0.5
            
            # 2. Confidence/Quality Score (if applicable)
            confidence_score = item.content.get("confidence", 1.0)
            
            # Combine
            final_score = (semantic_score * 0.7) + (confidence_score * 0.3)
            
            # Assign Ranking
            item.ranking = ContextRanking(
                semantic_score=semantic_score,
                confidence_score=confidence_score,
                final_score=final_score
            )
            
            # Assign Selection Reason
            item.selection = ContextSelection(
                reason=f"Matched {match_count} keywords.",
                selection_method="KEYWORD_MATCH" if match_count > 0 else "DEFAULT"
            )
