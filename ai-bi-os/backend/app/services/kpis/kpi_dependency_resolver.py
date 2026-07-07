from typing import Dict, List, Set

class KPIDependencyResolver:
    """Resolves execution order and detects circular dependencies for derived KPIs."""
    
    @staticmethod
    def resolve_execution_order(kpi_dependencies: Dict[str, List[str]]) -> List[str]:
        """
        Takes a dict of {kpi_id: [dependent_kpi_id_1, dependent_kpi_id_2]}
        Returns a sorted list of kpi_ids in the order they must be calculated.
        Raises ValueError on circular dependencies.
        """
        visited: Set[str] = set()
        path: Set[str] = set()
        order: List[str] = []
        
        def dfs(node: str):
            if node in path:
                raise ValueError(f"Circular dependency detected involving KPI: {node}")
            if node in visited:
                return
                
            path.add(node)
            for dep in kpi_dependencies.get(node, []):
                dfs(dep)
            path.remove(node)
            
            visited.add(node)
            order.append(node)
            
        for kpi_id in kpi_dependencies:
            if kpi_id not in visited:
                dfs(kpi_id)
                
        return order
