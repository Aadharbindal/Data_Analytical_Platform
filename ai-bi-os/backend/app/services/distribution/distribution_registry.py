import logging
from typing import List

logger = logging.getLogger("DistributionRegistry")

class DistributionRegistry:
    """Registers supported statistical distributions."""
    
    def __init__(self):
        self.supported_distributions = [
            "NORMAL", "UNIFORM", "BINOMIAL", "POISSON", "EXPONENTIAL",
            "GAMMA", "BETA", "LOG_NORMAL", "WEIBULL", "CHI_SQUARE",
            "STUDENT_T", "LOGISTIC", "LAPLACE", "GEOMETRIC", "NEGATIVE_BINOMIAL"
        ]
        
    def is_supported(self, dist_name: str) -> bool:
        return dist_name.upper() in self.supported_distributions
        
    def get_supported_distributions(self) -> List[str]:
        return self.supported_distributions

distribution_registry = DistributionRegistry()
