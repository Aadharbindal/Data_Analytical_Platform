import logging
from typing import List, Dict, Any

from app.services.statistics.inference_registry import inference_registry
from app.services.statistics.inference_validator import inference_validator

logger = logging.getLogger("InferencePlanner")

class InferencePlanner:
    """
    Plans the execution of hypothesis tests by validating assumptions and picking tests.
    """
    
    def plan_hypothesis_tests(self, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Constructs an execution plan. For MVP, we assume a simplified scenario where 
        we want to test if each metric is significantly different from 0.
        """
        tasks = []
        for metric in metrics:
            if metric["type"] != "NUMERIC":
                continue
                
            normal = inference_validator.check_normality(metric.get("stats", {}))
            
            test_type = inference_registry.determine_hypothesis_test(
                groups_count=1, normal=normal, equal_variance=True
            )
            
            tasks.append({
                "target_metric": metric["name"],
                "test_name": test_type,
                "null_hypothesis_value": 0
            })
            
        return tasks

inference_planner = InferencePlanner()
