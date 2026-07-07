from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.forecast_governance import ForecastMonitoring

class ForecastMonitor:
    def log_monitoring_metrics(
        self,
        db: Session,
        model_id: str,
        accuracy: float = None,
        drift_score: float = None,
        latency_ms: float = None,
        forecast_error: float = None,
        prediction_confidence: float = None,
        usage_increment: int = 1,
        failures_increment: int = 0
    ) -> ForecastMonitoring:
        """
        Create a monitoring log entry for the model.
        """
        monitoring_log = ForecastMonitoring(
            model_id=model_id,
            accuracy=accuracy,
            drift_score=drift_score,
            latency_ms=latency_ms,
            forecast_error=forecast_error,
            prediction_confidence=prediction_confidence,
            usage_count=usage_increment,
            failures_count=failures_increment
        )
        db.add(monitoring_log)
        db.commit()
        db.refresh(monitoring_log)
        return monitoring_log

forecast_monitor = ForecastMonitor()
