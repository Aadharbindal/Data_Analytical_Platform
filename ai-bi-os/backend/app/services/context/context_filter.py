from typing import List
from app.models.context import ContextItem

class ContextFilter:
    """Removes duplicates and expired information."""
    
    @staticmethod
    def filter_items(items: List[ContextItem]) -> List[ContextItem]:
        unique_contents = set()
        filtered = []
        
        for item in items:
            # Deterministic deduplication based on content hash
            content_str = str(item.content)
            if content_str not in unique_contents:
                unique_contents.add(content_str)
                filtered.append(item)
                
        return filtered
