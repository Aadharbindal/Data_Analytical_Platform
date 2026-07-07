import numpy as np
from typing import List, Dict, Any
from app.services.forecast_governance.evaluation_service import evaluation_service

class BenchmarkEngine:
    def calculate_benchmarks(self, actuals: List[float], predictions: List[float]) -> Dict[str, Any]:
        """
        Calculate benchmarks such as Naive Forecast (last value carries forward) and Moving Average (e.g. window=3).
        """
        if len(actuals) < 2:
            return {}

        # Naive forecast: shifted by 1
        naive_preds = [actuals[0]] + actuals[:-1]
        naive_metrics = evaluation_service.evaluate_forecast(actuals, naive_preds)

        # Moving average forecast (window = min(3, len(actuals)))
        window = min(3, len(actuals))
        ma_preds = []
        for i in range(len(actuals)):
            if i < window:
                ma_preds.append(np.mean(actuals[:i+1]))
            else:
                ma_preds.append(np.mean(actuals[i-window:i]))
                
        ma_metrics = evaluation_service.evaluate_forecast(actuals, ma_preds)

        # Production model
        prod_metrics = evaluation_service.evaluate_forecast(actuals, predictions)

        return {
            "naive_mae": naive_metrics.get("mae"),
            "naive_rmse": naive_metrics.get("rmse"),
            "ma_mae": ma_metrics.get("mae"),
            "ma_rmse": ma_metrics.get("rmse"),
            "prod_model_mae": prod_metrics.get("mae"),
            "prod_model_rmse": prod_metrics.get("rmse"),
            "historical_best_mae": None, # would come from DB historical records
            "historical_best_rmse": None
        }

benchmark_engine = BenchmarkEngine()
