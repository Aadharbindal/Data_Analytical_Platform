import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import time

from app.services.correlation.correlation_planner import correlation_planner
from app.services.correlation.correlation_executor import correlation_executor
from app.services.correlation.correlation_repository import correlation_repository

logger = logging.getLogger("CorrelationService")

class CorrelationService:
    """Main orchestrator for Correlation Engine."""
    
    def run_correlation(self, db: Session, dataset_id: str, dataset_version_id: str, 
                        columns_meta: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        logger.info(f"Starting Correlation Run for Dataset {dataset_id}")
        start_time = time.time()
        
        # 1. Setup DB Tracking
        run = correlation_repository.create_run(db, dataset_id, dataset_version_id)
        run.status = "PROCESSING"
        db.commit()
        
        try:
            # 2. Plan
            tasks = correlation_planner.create_execution_plan(columns_meta)
            
            # 3. Execute
            table_name = f"dataset_{dataset_version_id.replace('-', '_')}"
            results = correlation_executor.execute_tasks(table_name, tasks)
            
            # 4. Save Numerical Results
            for num_res in results["numerical_results"]:
                correlation_repository.save_numeric_correlation(db, run.id, num_res)
                
            # 5. Save Association Results
            for assoc_res in results["association_results"]:
                correlation_repository.save_association(db, run.id, assoc_res)
                
            # 6. Save Feature Relationships
            for feat_rel in results["feature_relationships"]:
                correlation_repository.save_feature_relationship(db, run.id, feat_rel)
                
            # 7. Finalize Run
            run.status = "COMPLETED"
            run.execution_time_ms = results["execution_time_ms"]
            run.pairs_evaluated = len(tasks)
            run.significant_relationships_found = len(results["feature_relationships"])
            
            correlation_repository.log_history(db, dataset_version_id, "COMPLETED", run.execution_time_ms)
            db.commit()
            
            return {
                "run_id": run.id,
                "status": "COMPLETED",
                "execution_time_ms": run.execution_time_ms,
                "pairs_evaluated": run.pairs_evaluated,
                "significant_relationships": run.significant_relationships_found
            }
            
        except Exception as e:
            run.status = "FAILED"
            db.commit()
            correlation_repository.log_history(db, dataset_version_id, "FAILED", errors={"error": str(e)})
            logger.error(f"Correlation Run failed: {e}")
            raise e

correlation_service = CorrelationService()
