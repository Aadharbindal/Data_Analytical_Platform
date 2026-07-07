from app.models.context import ContextPackage

class PromptOptimizer:
    """Deduplicates context references to save tokens before rendering."""
    
    @staticmethod
    def optimize(context_package: ContextPackage) -> None:
        # The Context Builder (Module 16) already does aggressive filtering and compression.
        # This optimizer can do structural cleanup specifically for prompting.
        
        seen_metrics = set()
        optimized_items = []
        
        for item in context_package.items:
            # Prevent sending the exact same metric value twice if sources overlap
            if item.source_type == "INSIGHT":
                metric_name = item.content.get("metric")
                if metric_name in seen_metrics:
                    continue # Skip redundant insight if we already have one for this metric
                seen_metrics.add(metric_name)
                
            optimized_items.append(item)
            
        context_package.items = optimized_items
