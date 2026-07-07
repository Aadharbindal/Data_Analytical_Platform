import logging
from typing import Dict, Any

logger = logging.getLogger("QualityAssessor")

class QualityAssessor:
    """
    Deterministically assesses fundamental data/model metrics (e.g., extracting R2, computing missing %).
    """
    
    def assess_metrics(self, target_type: str, metadata: Dict[str, Any]) -> Dict[str, float]:
        """
        Extracts and standardizes metrics from the payload.
        """
        metrics = {}
        
        # Base Data Quality
        metrics["missing_percentage"] = metadata.get("missing_percentage", 0.0)
        metrics["sample_size"] = metadata.get("sample_size", 100)
        
        if target_type == "REGRESSION":
            metrics["r_squared"] = metadata.get("r_squared", 0.0)
            metrics["rmse"] = metadata.get("rmse", 999.0)
        elif target_type == "STATISTICS":
            metrics["p_value"] = metadata.get("p_value", 1.0)
            
        return metrics

quality_assessor = QualityAssessor()
