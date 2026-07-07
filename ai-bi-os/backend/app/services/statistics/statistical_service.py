import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import time

from app.services.statistics.inference_planner import inference_planner
from app.services.statistics.inference_executor import inference_executor
from app.services.statistics.inference_repository import inference_repository

logger = logging.getLogger("StatisticalService")

class StatisticalService:
    """Main orchestrator for Statistical Inference Engine."""
    
    def run_statistics(self, db: Session, dataset_id: str, dataset_version_id: str, 
                       population_size: int, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        logger.info(f"Starting Statistical Run for Dataset {dataset_id}")
        
        # 1. Setup DB Tracking
        run = inference_repository.create_run(db, dataset_id, dataset_version_id)
        run.status = "PROCESSING"
        db.commit()
        
        try:
            # 2. Plan
            hypothesis_plan = inference_planner.plan_hypothesis_tests(metrics)
            
            # 3. Execute all engines
            results = inference_executor.execute_plan(population_size, hypothesis_plan, metrics)
            
            # 4. Save Results
            for h in results["hypothesis_results"]:
                inference_repository.save_hypothesis_test(db, run.id, h)
                
            for c in results["confidence_results"]:
                inference_repository.save_confidence_interval(db, run.id, c)
                
            for d in results["distribution_results"]:
                inference_repository.save_distribution_profile(db, run.id, d)
                
            inference_repository.save_sampling_profile(db, run.id, results["sampling_profile"])
            
            for p in results["probability_results"]:
                inference_repository.save_probability_result(db, run.id, p)
                
            for i in results["inference_results"]:
                inference_repository.save_inference_result(db, run.id, i)
                
            # 5. Finalize Run
            run.status = "COMPLETED"
            run.execution_time_ms = results["execution_time_ms"]
            run.total_tests_run = len(hypothesis_plan)
            run.significant_results_found = len([h for h in results["hypothesis_results"] if h["reject_null_hypothesis"]])
            
            inference_repository.log_history(db, dataset_version_id, "COMPLETED", run.execution_time_ms)
            db.commit()
            
            return {
                "run_id": run.id,
                "status": "COMPLETED",
                "execution_time_ms": run.execution_time_ms,
                "total_tests_run": run.total_tests_run,
                "significant_results_found": run.significant_results_found
            }
            
        except Exception as e:
            run.status = "FAILED"
            db.commit()
            inference_repository.log_history(db, dataset_version_id, "FAILED")
            logger.error(f"Statistical Run failed: {e}")
            raise e

statistical_service = StatisticalService()
