import logging
from typing import Dict, Any, List

logger = logging.getLogger("PredictionEngine")

class PredictionEngine:
    """
    Handles batch/single predictions deterministically directly from DB results.
    Avoids loading binary pickles.
    """
    
    def predict(self, intercept: float, coefficients: Dict[str, float], 
                inputs: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """
        Applies y = sum(x_i * beta_i) + alpha
        """
        predictions = []
        
        for input_row in inputs:
            y_pred = intercept
            for feat, val in input_row.items():
                if feat in coefficients:
                    y_pred += val * coefficients[feat]
                    
            predictions.append({
                "input_features": input_row,
                "predicted_value": round(y_pred, 4),
                "confidence_lower": round(y_pred - 1.5, 4), # Mock 95% CI
                "confidence_upper": round(y_pred + 1.5, 4)
            })
            
        return predictions

prediction_engine = PredictionEngine()
