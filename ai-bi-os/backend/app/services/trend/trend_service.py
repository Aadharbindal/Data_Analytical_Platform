import logging
import time
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.services.trend.trend_validator import trend_validator
from app.services.trend.trend_analyzer import trend_analyzer
from app.services.trend.growth_analyzer import growth_analyzer
from app.services.trend.decline_analyzer import decline_analyzer
from app.services.trend.change_point_detector import change_point_detector
from app.services.trend.trend_repository import trend_repository

logger = logging.getLogger("TrendService")

class TrendService:
    """Main orchestrator for Trend Engine."""
    
    def run_trend_analysis(self, db: Session, dataset_id: str, dataset_version_id: str, 
                               columns: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        start_time = time.time()
        logger.info(f"Starting Trend Analysis for Dataset {dataset_id}")
        
        run = trend_repository.create_run(db, dataset_id, dataset_version_id)
        run.status = "PROCESSING"
        trend_repository.log_history(db, run.id, "STARTED")
        
        processed_count = 0
        total_inc = 0
        total_dec = 0
        total_cp = 0
        
        try:
            for col in columns:
                col_name = col["name"]
                
                # 1. Validation
                validations = trend_validator.validate_trend_signal(col)
                # Skip if minimum window fails
                if not all(v["passed"] for v in validations if v["check_name"] == "MIN_WINDOW"):
                    continue
                
                # 2. Overall Profile
                profile_data = trend_analyzer.generate_profile(col)
                profile_data["column_name"] = col_name
                profile_data["metric_name"] = col.get("metric_name")
                
                profile = trend_repository.save_profile(db, run.id, profile_data)
                
                for v in validations:
                    trend_repository.log_validation(db, profile.id, v)
                    
                # 3. Growth/Decline Segments
                growth_segs = growth_analyzer.extract_growth_segments(col)
                for g in growth_segs:
                    trend_repository.save_segment(db, profile.id, g)
                    total_inc += 1
                    
                decline_segs = decline_analyzer.extract_decline_segments(col)
                for d in decline_segs:
                    trend_repository.save_segment(db, profile.id, d)
                    total_dec += 1
                    
                # 4. Change Points
                cps = change_point_detector.detect_change_points(col)
                for cp in cps:
                    trend_repository.save_change_point(db, profile.id, cp)
                    total_cp += 1
                    
                processed_count += 1
                
            run.status = "COMPLETED"
            run.series_processed = processed_count
            run.execution_time_ms = (time.time() - start_time) * 1000
            
            trend_repository.save_summary(db, run.id, {
                "column_name": None,
                "increasing_segments": total_inc,
                "decreasing_segments": total_dec,
                "total_change_points": total_cp
            })
            
            trend_repository.log_history(db, run.id, "COMPLETED")
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
            trend_repository.log_history(db, run.id, "FAILED")
            logger.error(f"Trend Analysis failed: {e}")
            raise e

trend_service = TrendService()
