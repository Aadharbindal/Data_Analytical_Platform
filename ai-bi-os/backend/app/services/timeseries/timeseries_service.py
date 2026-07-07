import logging
import time
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.services.timeseries.temporal_validator import temporal_validator
from app.services.timeseries.frequency_detector import frequency_detector
from app.services.timeseries.gap_detection_engine import gap_detection_engine
from app.services.timeseries.window_engine import window_engine
from app.services.timeseries.timeseries_analyzer import timeseries_analyzer
from app.services.timeseries.timeseries_repository import timeseries_repository

logger = logging.getLogger("TimeSeriesService")

class TimeSeriesService:
    """Main orchestrator for TimeSeries Analytics Engine."""
    
    def run_temporal_analysis(self, db: Session, dataset_id: str, dataset_version_id: str, 
                                  columns: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        start_time = time.time()
        logger.info(f"Starting Temporal Analysis for Dataset {dataset_id}")
        
        run = timeseries_repository.create_run(db, dataset_id, dataset_version_id)
        run.status = "PROCESSING"
        timeseries_repository.log_history(db, run.id, "STARTED")
        
        processed_count = 0
        
        try:
            for col in columns:
                col_name = col["name"]
                
                # 1. Frequency Detection
                freq_data = frequency_detector.detect_frequency(col)
                freq_conf = freq_data.get("frequency_confidence", 100.0)
                
                # 2. Gap Analysis
                gap_data = gap_detection_engine.analyze_gaps(freq_data.get("inferred_frequency", "MIXED"), col)
                cont_score = gap_data.get("continuity_score", 100.0)
                
                # 3. Profiling
                profile_data = timeseries_analyzer.generate_profile(col_name, col, freq_conf, cont_score)
                profile = timeseries_repository.save_profile(db, run.id, profile_data)
                
                # Link children
                timeseries_repository.save_frequency(db, profile.id, freq_data)
                timeseries_repository.save_gaps(db, profile.id, gap_data)
                
                # 4. Validations (Duplicates, Order)
                validations = temporal_validator.validate_time_column(col)
                for v in validations:
                    timeseries_repository.log_validation(db, profile.id, v)
                    
                # 5. Execute Windows
                windows = window_engine.calculate_windows(col)
                for w in windows:
                    timeseries_repository.save_window(db, profile.id, w)
                    
                processed_count += 1
                    
            run.status = "COMPLETED"
            run.series_processed = processed_count
            run.execution_time_ms = (time.time() - start_time) * 1000
            
            timeseries_repository.log_history(db, run.id, "COMPLETED")
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
            timeseries_repository.log_history(db, run.id, "FAILED")
            logger.error(f"TimeSeries Analysis failed: {e}")
            raise e

timeseries_service = TimeSeriesService()
