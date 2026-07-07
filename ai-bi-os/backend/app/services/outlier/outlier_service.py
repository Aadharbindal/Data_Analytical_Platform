import logging
import time
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.services.outlier.outlier_validator import outlier_validator
from app.services.outlier.outlier_detector import outlier_detector
from app.services.outlier.extreme_value_analyzer import extreme_value_analyzer
from app.services.outlier.business_rule_filter import business_rule_filter
from app.services.outlier.outlier_repository import outlier_repository

logger = logging.getLogger("OutlierService")

class OutlierService:
    """Main orchestrator for Outlier Analysis Engine."""
    
    def run_outlier_analysis(self, db: Session, dataset_id: str, dataset_version_id: str, 
                                  columns: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        start_time = time.time()
        logger.info(f"Starting Outlier Analysis for Dataset {dataset_id}")
        
        run = outlier_repository.create_run(db, dataset_id, dataset_version_id)
        run.status = "PROCESSING"
        outlier_repository.log_history(db, run.id, "STARTED")
        
        processed_count = 0
        total_outliers = 0
        
        try:
            for col in columns:
                col_name = col["name"]
                
                if col.get("type", "NUMERICAL") != "NUMERICAL":
                    continue
                    
                try:
                    # 1. Validation
                    outlier_validator.validate_for_detection(col)
                    outlier_repository.log_validation(db, run.id, col_name, "MIN_SAMPLE_SIZE", True)
                    
                    raw_vals = col.get("raw_values", []) # Mock array passed in metadata
                    if not raw_vals: continue
                    
                    # 2. Detect Outliers
                    outliers = outlier_detector.detect_outliers(col, raw_vals, method="IQR")
                    
                    # 3. Assess Severity & Save
                    for o in outliers:
                        severity_info = business_rule_filter.assess_severity(o, col)
                        o.update(severity_info)
                        outlier_repository.save_outlier(db, run.id, col_name, o)
                        total_outliers += 1
                        
                    # 4. Extreme Values
                    extremes = extreme_value_analyzer.extract_extreme_values(col, raw_vals)
                    for e in extremes:
                        outlier_repository.save_extreme(db, run.id, col_name, e)
                        
                    # 5. Summarize Column
                    outlier_repository.save_summary(db, run.id, {
                        "column_name": col_name,
                        "total_outliers": len(outliers),
                        "outlier_percentage": (len(outliers) / len(raw_vals)) * 100 if raw_vals else 0
                    })
                    
                    processed_count += 1
                except ValueError as ve:
                    outlier_repository.log_validation(db, run.id, col_name, "MIN_SAMPLE_SIZE", False, str(ve))
                    logger.warning(f"Skipping col {col_name}: {ve}")
                    continue
                    
            run.status = "COMPLETED"
            run.rows_processed = processed_count # Mapped to cols processed in this mock
            run.execution_time_ms = (time.time() - start_time) * 1000
            
            # Save Dataset Summary
            outlier_repository.save_summary(db, run.id, {
                "column_name": None,
                "total_outliers": total_outliers,
                "outlier_percentage": 0.0 # Aggregate
            })
            
            outlier_repository.log_history(db, run.id, "COMPLETED")
            db.commit()
            
            return {
                "run_id": run.id,
                "status": run.status,
                "total_outliers": total_outliers,
                "execution_time_ms": run.execution_time_ms
            }
            
        except Exception as e:
            run.status = "FAILED"
            db.commit()
            outlier_repository.log_history(db, run.id, "FAILED")
            logger.error(f"Outlier Analysis failed: {e}")
            raise e

outlier_service = OutlierService()
