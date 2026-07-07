import logging
import time
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.services.forecast.forecast_validator import forecast_validator
from app.services.forecast.forecast_model_selector import forecast_model_selector
from app.services.forecast.backtesting_engine import backtesting_engine
from app.services.forecast.forecast_executor import forecast_executor
from app.services.forecast.forecast_planner import forecast_planner
from app.services.forecast.forecast_repository import forecast_repository

logger = logging.getLogger("ForecastService")

class ForecastService:
    """Main orchestrator for Forecasting Engine."""
    
    def run_forecast_analysis(self, db: Session, dataset_id: str, dataset_version_id: str, 
                                  metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        start_time = time.time()
        logger.info(f"Starting Forecast Analysis for Dataset {dataset_id}")
        
        run = forecast_repository.create_run(db, dataset_id, dataset_version_id)
        run.status = "PROCESSING"
        forecast_repository.log_history(db, run.id, "STARTED")
        
        processed_count = 0
        
        try:
            for met in metrics:
                col_name = met["column_name"]
                
                # 1. Validation (must pass all)
                validations = forecast_validator.validate_series(met)
                
                # We will register models even if they fail just to track them
                # But in reality we might skip predictions
                
                # 2. Select Best Model among candidates
                candidates = met.get("candidate_models", [])
                if not candidates:
                    continue
                    
                best_model = forecast_model_selector.select_best_model(candidates)
                
                for cand in candidates:
                    # Save DB Model
                    is_best = (cand["model_name"] == best_model["model_name"])
                    m = forecast_repository.save_model(db, run.id, {
                        "column_name": col_name,
                        "model_name": cand["model_name"],
                        "is_selected": is_best,
                        "aic": cand.get("aic"),
                        "rmse": cand.get("rmse")
                    })
                    
                    # Log Validations under this model
                    for v in validations:
                        forecast_repository.log_validation(db, m.id, v)
                        
                    # 3. If selected, run backtest, prediction, and scenarios
                    if is_best:
                        acc = backtesting_engine.simulate_backtest(cand)
                        forecast_repository.save_accuracy(db, m.id, acc)
                        
                        preds = forecast_executor.execute_horizon(cand)
                        forecast_repository.save_predictions(db, m.id, preds)
                        
                        # 4. Scenarios
                        scenarios = forecast_planner.generate_scenarios(preds["prediction_series"])
                        for sc in scenarios:
                            forecast_repository.save_scenario(db, m.id, sc)
                            
                processed_count += 1
                
            run.status = "COMPLETED"
            run.series_processed = processed_count
            run.execution_time_ms = (time.time() - start_time) * 1000
            
            forecast_repository.log_history(db, run.id, "COMPLETED")
            db.commit()
            
            return {
                "run_id": run.id,
                "status": run.status,
                "series_processed": processed_count,
                "execution_time_ms": run.execution_time_ms
            }
            
        except Exception as e:
            run.status = "FAILED"
            db.commit()
            forecast_repository.log_history(db, run.id, "FAILED")
            logger.error(f"Forecast Analysis failed: {e}")
            raise e

forecast_service = ForecastService()
