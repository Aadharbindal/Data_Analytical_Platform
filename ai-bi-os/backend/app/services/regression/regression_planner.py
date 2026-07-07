import logging
from typing import List, Dict, Any

from app.services.regression.regression_validator import regression_validator

logger = logging.getLogger("RegressionPlanner")

class RegressionPlanner:
    """
    Handles feature selection planning (Forward, Backward, Filter methods).
    """
    
    def plan_feature_selection(self, all_features: List[str], target: str, 
                               selection_method: str = "ALL") -> List[str]:
        """
        Determines which features to include in the model.
        """
        features_to_use = [f for f in all_features if f != target]
        
        if selection_method == "FORWARD":
            # Mock forward selection logic
            pass
        elif selection_method == "CORRELATION_FILTERING":
            # Keep only highly correlated features
            pass
            
        logger.info(f"Planned regression with {len(features_to_use)} features using {selection_method}.")
        return features_to_use

regression_planner = RegressionPlanner()
