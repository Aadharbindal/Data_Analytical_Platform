import logging
from typing import List, Dict, Any

from app.services.eda.eda_registry import eda_registry

logger = logging.getLogger("EDAPlanner")

class EDAPlanner:
    """
    Determines which statistical analyses to run per column based on data types.
    Constructs an execution plan.
    """
    
    def create_execution_plan(self, schema_info: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Input: [{'name': 'revenue', 'type': 'NUMERIC'}, ...]
        Output: Plan of what to run per column
        """
        plan = {
            "dataset_level": ["row_count", "col_count", "memory"],
            "column_level": {}
        }
        
        for col in schema_info:
            col_name = col["name"]
            data_type = col["type"]
            
            analyzers = eda_registry.get_analyzers_for_type(data_type)
            
            # Universal column stats
            col_plan = {
                "type": data_type,
                "universal": ["null_count", "distinct_count", "memory_usage"],
                "specific": analyzers
            }
            
            plan["column_level"][col_name] = col_plan
            
        logger.info(f"Created EDA Execution Plan for {len(schema_info)} columns.")
        return plan

eda_planner = EDAPlanner()
