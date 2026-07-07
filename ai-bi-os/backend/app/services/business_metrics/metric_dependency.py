import logging
from typing import List, Dict, Set

logger = logging.getLogger("MetricDependency")

class MetricDependencyResolver:
    """
    Resolves the DAG (Directed Acyclic Graph) of nested metric dependencies.
    Prevents circular references.
    """
    
    def __init__(self):
        # adjacency list: metric_id -> list of metric_ids it depends on
        self._graph: Dict[str, List[str]] = {}
        
    def add_dependency(self, metric_id: str, depends_on: List[str]):
        """Adds a metric and its dependencies to the graph."""
        self._graph[metric_id] = depends_on
        
    def check_circular(self, metric_id: str, depends_on: List[str]) -> bool:
        """
        Temporarily adds the dependency and checks for cycles using DFS.
        Returns True if a cycle is detected.
        """
        # Save current state
        original = self._graph.get(metric_id, [])
        self._graph[metric_id] = depends_on
        
        try:
            visited = set()
            path = set()
            
            def dfs(node: str) -> bool:
                if node in path:
                    return True # Cycle detected
                if node in visited:
                    return False
                    
                visited.add(node)
                path.add(node)
                
                for neighbor in self._graph.get(node, []):
                    if dfs(neighbor):
                        return True
                        
                path.remove(node)
                return False
                
            # Check for cycles from the newly added node
            has_cycle = dfs(metric_id)
            return has_cycle
            
        finally:
            # Restore state
            self._graph[metric_id] = original

    def get_execution_order(self, target_metric_id: str) -> List[str]:
        """
        Returns a topological sort of the dependencies for a given metric.
        Determines the order in which derived metrics must be calculated.
        """
        visited = set()
        order = []
        
        def dfs(node: str):
            if node in visited:
                return
            visited.add(node)
            for neighbor in self._graph.get(node, []):
                dfs(neighbor)
            order.append(node)
            
        dfs(target_metric_id)
        return order

metric_dependency = MetricDependencyResolver()
