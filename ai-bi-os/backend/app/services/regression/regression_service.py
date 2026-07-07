import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.services.regression.model_registry import model_registry
from app.services.regression.regression_validator import regression_validator
from app.services.regression.regression_planner import regression_planner
from app.services.regression.regression_executor import regression_executor
from app.services.regression.model_version_manager import model_version_manager
from app.services.regression.model_repository import model_repository
from app.services.regression.prediction_engine import prediction_engine

from app.models.regression import RegressionModel, RegressionRun

logger = logging.getLogger("RegressionService")

class RegressionService:
    """Main orchestrator for Regression Engine."""
    
    def train_model(self, db: Session, dataset_id: str, dataset_version_id: str,
                    model_name: str, algorithm: str, target_variable: str,
                    dataset_stats: Dict[str, Any], all_features: List[str]) -> Dict[str, Any]:
        
        logger.info(f"Starting Regression Training: {model_name} ({algorithm})")
        
        if not model_registry.is_supported(algorithm):
            raise ValueError(f"Algorithm {algorithm} is not supported.")
            
        regression_validator.validate_training_data(dataset_stats, all_features)
        features = regression_planner.plan_feature_selection(all_features, target_variable)
        
        # 1. DB Setup
        model = model_version_manager.get_or_create_model(db, dataset_id, model_name, algorithm, target_variable)
        version = model_version_manager.create_new_version(db, model.id)
        run = model_repository.create_run(db, model.id, dataset_version_id)
        run.status = "TRAINING"
        db.commit()
        
        try:
            # 2. Execute Training
            res = regression_executor.train_model(algorithm, features, target_variable)
            
            # 3. Save Results
            model_repository.save_result(db, run.id, res["intercept"], res["coefficients"])
            model_repository.save_metrics(db, run.id, res["metrics"])
            model_repository.save_feature_importance(db, run.id, res["feature_importance"])
            model_repository.save_residuals(db, run.id, res["residuals"])
            
            run.status = "COMPLETED"
            run.execution_time_ms = res["execution_time_ms"]
            model_repository.log_history(db, model.id, "TRAINED", {"version": version.version_number})
            db.commit()
            
            return {
                "model_id": model.id,
                "version": version.version_number,
                "run_id": run.id,
                "status": "COMPLETED",
                "metrics": res["metrics"]
            }
            
        except Exception as e:
            run.status = "FAILED"
            db.commit()
            model_repository.log_history(db, model.id, "TRAIN_FAILED", {"error": str(e)})
            raise e
            
    def predict(self, db: Session, model_id: str, inputs: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Makes predictions using the active version."""
        
        # Get active run
        run = db.query(RegressionRun).join(RegressionRun.model).filter(
            RegressionModel.id == model_id,
            RegressionRun.status == "COMPLETED"
        ).order_by(RegressionRun.created_at.desc()).first()
        
        if not run or not run.result:
            raise ValueError("No trained model found for prediction.")
            
        intercept = run.result.intercept
        coefficients = run.result.coefficients
        
        predictions = prediction_engine.predict(intercept, coefficients, inputs)
        
        # Log audit
        model_repository.save_predictions(db, run.id, predictions)
        db.commit()
        
        return predictions

regression_service = RegressionService()
