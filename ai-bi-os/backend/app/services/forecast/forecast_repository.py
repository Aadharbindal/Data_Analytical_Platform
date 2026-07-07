import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.forecast import (
    ForecastRun, ForecastModel, ForecastPrediction,
    ForecastScenario, ForecastAccuracy, ForecastValidation, ForecastHistory
)

logger = logging.getLogger("ForecastRepository")

class ForecastRepository:
    """DB operations for Forecast Engine."""
    
    def create_run(self, db: Session, dataset_id: str, dataset_version_id: str) -> ForecastRun:
        run = ForecastRun(dataset_id=dataset_id, dataset_version_id=dataset_version_id)
        db.add(run)
        db.flush()
        return run
        
    def save_model(self, db: Session, run_id: str, model_data: Dict[str, Any]) -> ForecastModel:
        m = ForecastModel(run_id=run_id, **model_data)
        db.add(m)
        db.flush()
        return m
        
    def save_predictions(self, db: Session, model_id: str, pred_data: Dict[str, Any]):
        p = ForecastPrediction(model_id=model_id, **pred_data)
        db.add(p)
        
    def save_scenario(self, db: Session, model_id: str, scenario_data: Dict[str, Any]):
        s = ForecastScenario(model_id=model_id, **scenario_data)
        db.add(s)
        
    def save_accuracy(self, db: Session, model_id: str, acc_data: Dict[str, Any]):
        a = ForecastAccuracy(model_id=model_id, **acc_data)
        db.add(a)
        
    def log_validation(self, db: Session, model_id: str, val_data: Dict[str, Any]):
        v = ForecastValidation(model_id=model_id, **val_data)
        db.add(v)
        
    def log_history(self, db: Session, run_id: str, action: str):
        h = ForecastHistory(run_id=run_id, action=action)
        db.add(h)
        db.commit()

forecast_repository = ForecastRepository()
