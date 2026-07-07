import logging
from typing import Dict, Any

logger = logging.getLogger("ConfidenceEngine")

class ConfidenceEngine:
    """Synthesizes percentage-based confidence scores based on sample size and metrics."""
    
    def calculate_confidence(self, target_type: str, metrics: Dict[str, float]) -> Dict[str, Any]:
        data_conf = max(0, 100 - (metrics.get("missing_percentage", 0) * 2))
        
        stat_conf = 100.0
        model_conf = 100.0
        
        if target_type == "REGRESSION":
            model_conf = max(0, metrics.get("r_squared", 0) * 100)
            
        if target_type == "STATISTICS":
            p = metrics.get("p_value", 1)
            stat_conf = 100 if p < 0.05 else 50
            
        overall = (data_conf + stat_conf + model_conf) / 3.0
        
        grade = "A"
        if overall < 90: grade = "B"
        if overall < 80: grade = "C"
        if overall < 70: grade = "D"
        if overall < 60: grade = "F"
        
        return {
            "overall_confidence": overall,
            "data_confidence": data_conf,
            "statistical_confidence": stat_conf,
            "model_confidence": model_conf,
            "business_confidence": overall * 0.9,
            "prediction_confidence": model_conf,
            "confidence_level": "HIGH" if overall > 80 else "LOW",
            "confidence_grade": grade
        }

confidence_engine = ConfidenceEngine()
