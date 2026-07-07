import logging
from typing import List

logger = logging.getLogger("ModelRegistry")

class ModelRegistry:
    """
    Registers supported regression algorithms.
    """
    
    def __init__(self):
        self.supported_models = {
            "LINEAR_REGRESSION": "Ordinary Least Squares (OLS) Linear Regression",
            "RIDGE_REGRESSION": "Ridge (L2) Regression for handling multicollinearity",
            "LASSO_REGRESSION": "Lasso (L1) Regression for feature selection",
            "ELASTIC_NET": "Elastic Net (L1 + L2) Regression",
            "LOGISTIC_REGRESSION": "Logistic Regression for binary classification outcomes",
            "POLYNOMIAL_REGRESSION": "Polynomial Regression for non-linear relationships"
        }
        
    def is_supported(self, algorithm: str) -> bool:
        return algorithm.upper() in self.supported_models
        
    def get_supported_algorithms(self) -> List[str]:
        return list(self.supported_models.keys())

model_registry = ModelRegistry()
