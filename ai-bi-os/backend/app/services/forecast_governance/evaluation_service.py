import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from typing import List, Dict

class EvaluationService:
    def evaluate_forecast(self, actuals: List[float], predictions: List[float]) -> Dict[str, float]:
        """
        Calculate MAE, RMSE, MAPE, SMAPE, WMAPE, MSE, Bias, Error, Variance, Prediction Coverage
        """
        y_true = np.array(actuals)
        y_pred = np.array(predictions)
        
        # Guard against zero-length arrays or division by zero
        if len(y_true) == 0 or len(y_pred) == 0:
            return {}

        mae = float(mean_absolute_error(y_true, y_pred))
        mse = float(mean_squared_error(y_true, y_pred))
        rmse = float(np.sqrt(mse))
        
        # MAPE with guard against exactly zero actuals (handled by sklearn with large numbers, but we can do our own if needed, we'll use sklearn)
        try:
            mape = float(mean_absolute_percentage_error(y_true, y_pred))
        except:
            mape = 0.0

        # SMAPE
        denominator = (np.abs(y_true) + np.abs(y_pred)) / 2.0
        # Prevent division by zero
        smape_array = np.where(denominator != 0, np.abs(y_pred - y_true) / denominator, 0)
        smape = float(np.mean(smape_array))

        # WMAPE
        sum_abs_actuals = np.sum(np.abs(y_true))
        if sum_abs_actuals != 0:
            wmape = float(np.sum(np.abs(y_true - y_pred)) / sum_abs_actuals)
        else:
            wmape = 0.0

        # Bias (Mean Forecast Error)
        bias = float(np.mean(y_pred - y_true))

        # Forecast Error (could be same as bias or sum of errors)
        forecast_error = float(np.sum(y_pred - y_true))

        # Forecast Variance (variance of the errors)
        forecast_variance = float(np.var(y_pred - y_true))
        
        # Prediction Coverage (percentage of predictions within a typical confidence interval - proxy here by percentage within 20% error)
        coverage_array = np.where(np.abs(y_pred - y_true) <= (0.2 * np.abs(y_true)), 1, 0)
        prediction_coverage = float(np.mean(coverage_array)) if len(y_true) > 0 else 0.0

        return {
            "mae": mae,
            "rmse": rmse,
            "mape": mape,
            "smape": smape,
            "wmape": wmape,
            "mse": mse,
            "bias": bias,
            "forecast_error": forecast_error,
            "forecast_variance": forecast_variance,
            "prediction_coverage": prediction_coverage
        }

evaluation_service = EvaluationService()
