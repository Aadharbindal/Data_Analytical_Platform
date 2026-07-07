import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.regression import (
    RegressionModel, ModelVersion, RegressionRun, RegressionResult,
    ModelMetrics, FeatureImportance, ResidualAnalysis, Prediction, RegressionHistory
)

logger = logging.getLogger("ModelRepository")

class ModelRepository:
    """DB operations for Regression Models."""
    
    def create_model(self, db: Session, dataset_id: str, name: str, algorithm: str, target: str) -> RegressionModel:
        m = RegressionModel(dataset_id=dataset_id, name=name, algorithm=algorithm, target_variable=target)
        db.add(m)
        db.flush()
        return m
        
    def create_version(self, db: Session, model_id: str, version_number: int) -> ModelVersion:
        v = ModelVersion(model_id=model_id, version_number=version_number)
        db.add(v)
        db.flush()
        return v
        
    def create_run(self, db: Session, model_id: str, dataset_version_id: str) -> RegressionRun:
        run = RegressionRun(model_id=model_id, dataset_version_id=dataset_version_id)
        db.add(run)
        db.flush()
        return run
        
    def save_result(self, db: Session, run_id: str, intercept: float, coefficients: Dict[str, float]):
        res = RegressionResult(run_id=run_id, intercept=intercept, coefficients=coefficients)
        db.add(res)
        
    def save_metrics(self, db: Session, run_id: str, metrics: Dict[str, float]):
        m = ModelMetrics(run_id=run_id, **metrics)
        db.add(m)
        
    def save_feature_importance(self, db: Session, run_id: str, importances: List[Dict[str, Any]]):
        for imp in importances:
            fi = FeatureImportance(run_id=run_id, **imp)
            db.add(fi)
            
    def save_residuals(self, db: Session, run_id: str, residuals: Dict[str, Any]):
        ra = ResidualAnalysis(run_id=run_id, **residuals)
        db.add(ra)
        
    def save_predictions(self, db: Session, run_id: str, predictions: List[Dict[str, Any]]):
        for p in predictions:
            pred = Prediction(run_id=run_id, **p)
            db.add(pred)
            
    def log_history(self, db: Session, model_id: str, action: str, details: Dict = None):
        h = RegressionHistory(model_id=model_id, action=action, details=details)
        db.add(h)
        db.commit()

model_repository = ModelRepository()
