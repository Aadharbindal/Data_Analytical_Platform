from typing import List
from app.models.context import ContextItem

class ContextCompressor:
    """Truncates lists and drops low-ranked items to fit the Token Budget."""
    
    @staticmethod
    def compress(items: List[ContextItem], token_budget: int) -> List[ContextItem]:
        # Sort by rank descending
        items.sort(key=lambda x: x.ranking.final_score if x.ranking else 0, reverse=True)
        
        compressed = []
        current_tokens = 0
        
        for item in items:
            if current_tokens + item.estimated_tokens <= token_budget:
                compressed.append(item)
                current_tokens += item.estimated_tokens
            else:
                # Reached budget
                break
                
        return compressed
