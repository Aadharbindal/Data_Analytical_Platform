import logging
from typing import List, Dict, Any, Tuple

from app.services.correlation.correlation_registry import correlation_registry
from app.services.correlation.correlation_validator import correlation_validator

logger = logging.getLogger("CorrelationPlanner")

class CorrelationPlanner:
    """
    Plans pairwise combinations, filters invalid ones, and groups them by method.
    Prevents O(N^2) explosion by intelligently pruning pairs.
    """
    
    def create_execution_plan(self, columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes column metadata and creates a list of valid pairwise tasks.
        """
        tasks = []
        n = len(columns)
        
        for i in range(n):
            for j in range(i + 1, n):
                col_x = columns[i]
                col_y = columns[j]
                
                # 1. Validate pair feasibility
                if not correlation_validator.validate_pair(col_x, col_y):
                    continue
                    
                # 2. Determine Method
                method = correlation_registry.determine_method(col_x["type"], col_y["type"])
                
                if method != "UNKNOWN":
                    tasks.append({
                        "column_x": col_x["name"],
                        "column_y": col_y["name"],
                        "method": method,
                        "type_x": col_x["type"],
                        "type_y": col_y["type"]
                    })
                    
        logger.info(f"Planned {len(tasks)} pairwise correlation tasks from {n} columns.")
        return tasks

correlation_planner = CorrelationPlanner()
