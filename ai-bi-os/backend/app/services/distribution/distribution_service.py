import logging
import time
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.services.distribution.distribution_validator import distribution_validator
from app.services.distribution.distribution_analyzer import distribution_analyzer
from app.services.distribution.distribution_estimator import distribution_estimator
from app.services.distribution.goodness_of_fit_engine import goodness_of_fit_engine
from app.services.distribution.tail_analysis_engine import tail_analysis_engine
from app.services.distribution.distribution_repository import distribution_repository

logger = logging.getLogger("DistributionService")

class DistributionService:
    """Main orchestrator for Distribution Analytics Engine."""
    
    def run_distribution_analysis(self, db: Session, dataset_id: str, dataset_version_id: str, 
                                  columns: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        start_time = time.time()
        logger.info(f"Starting Distribution Analysis for Dataset {dataset_id}")
        
        run = distribution_repository.create_run(db, dataset_id, dataset_version_id)
        run.status = "PROCESSING"
        distribution_repository.log_history(db, run.id, "STARTED")
        
        processed_count = 0
        try:
            for col in columns:
                try:
                    # 1. Validation
                    distribution_validator.validate_for_fitting(col)
                    
                    # 2. Analyze Profile
                    profile_stats = distribution_analyzer.analyze_column(col)
                    profile_data = {
                        "column_name": col["name"],
                        "column_type": col.get("type", "NUMERICAL"),
                        **profile_stats
                    }
                    
                    profile = distribution_repository.save_profile(db, run.id, profile_data)
                    
                    # 3. Density Estimation
                    density = distribution_estimator.estimate_density(col)
                    distribution_repository.save_density(db, profile.id, density)
                    
                    # 4. Tail Analysis
                    tails = tail_analysis_engine.analyze_tails(profile_stats)
                    distribution_repository.save_tail_analysis(db, profile.id, tails)
                    
                    # 5. Fit Distributions & GOF
                    if col.get("type", "NUMERICAL") == "NUMERICAL":
                        fits = goodness_of_fit_engine.fit_and_rank(profile_stats)
                        for fit in fits:
                            distribution_repository.save_fit(db, profile.id, fit)
                    
                    processed_count += 1
                except ValueError as ve:
                    logger.warning(f"Skipping col {col['name']}: {ve}")
                    continue
                    
            run.status = "COMPLETED"
            run.columns_processed = processed_count
            run.execution_time_ms = (time.time() - start_time) * 1000
            
            distribution_repository.log_history(db, run.id, "COMPLETED")
            db.commit()
            
            return {
                "run_id": run.id,
                "status": run.status,
                "columns_processed": run.columns_processed,
                "execution_time_ms": run.execution_time_ms
            }
            
        except Exception as e:
            run.status = "FAILED"
            db.commit()
            distribution_repository.log_history(db, run.id, "FAILED")
            logger.error(f"Distribution Analysis failed: {e}")
            raise e

distribution_service = DistributionService()
