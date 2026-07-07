import logging
import time
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime

from app.models.business_metrics import MetricExecution
from app.services.business_metrics.metric_registry import metric_registry
from app.services.business_metrics.metric_validator import metric_validator
from app.services.business_metrics.metric_calculator import metric_calculator
from app.services.business_metrics.metric_cache import metric_cache_manager

logger = logging.getLogger("BusinessMetricsService")

class BusinessMetricsService:
    """
    Main orchestrator for defining, calculating, and managing business metrics.
    """
    
    def calculate_metric(self, db: Session, metric_id: str, dataset_version_id: str, 
                         dimension: str = None, dimension_value: str = None, 
                         time_window: str = None, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Calculates a metric, utilizing intelligent caching.
        """
        start_time = time.time()
        
        # 1. Check Registry
        metric_meta = metric_registry.get_metric(metric_id)
        if not metric_meta:
            raise ValueError(f"Metric {metric_id} not found in registry.")
            
        formula = metric_meta["formula"]
        
        # 2. Validate Request
        if dimension and dimension not in metric_meta.get("supported_dimensions", []):
            raise ValueError(f"Dimension {dimension} not supported for metric {metric_id}")
            
        # 3. Check Cache
        cache_key = metric_cache_manager.generate_cache_key(
            metric_id, dataset_version_id, dimension, dimension_value, time_window
        )
        
        if not force_refresh:
            cached_val = metric_cache_manager.get_cached_result(db, cache_key)
            if cached_val is not None:
                logger.info(f"Cache HIT for {cache_key}")
                self._log_execution(db, metric_id, time.time() - start_time, True, "SUCCESS")
                return {"value": cached_val, "cached": True}
                
        # 4. Calculate
        logger.info(f"Cache MISS for {cache_key}. Calculating...")
        dataset_table_name = f"dataset_{dataset_version_id.replace('-', '_')}"
        
        calc_result = metric_calculator.calculate(formula, dataset_table_name, dimension)
        
        if calc_result["status"] == "error":
            self._log_execution(db, metric_id, calc_result["execution_time_ms"], False, "FAILED", calc_result["error"])
            raise Exception(f"Calculation failed: {calc_result['error']}")
            
        # Extract specific dimension value if requested, else total
        if dimension_value and dimension:
            final_val = calc_result["data"].get(dimension_value, 0.0)
        elif not dimension:
            final_val = calc_result["data"].get("total", 0.0)
        else:
            final_val = calc_result["data"] # Return all dimensional splits
            
        # 5. Cache scalar results
        if isinstance(final_val, (int, float)):
            metric_cache_manager.set_cached_result(
                db, metric_id, dataset_version_id, cache_key, float(final_val)
            )
            
        self._log_execution(db, metric_id, time.time() - start_time, False, "SUCCESS")
        
        return {"value": final_val, "cached": False}
        
    def _log_execution(self, db: Session, metric_id: str, exec_time_s: float, was_cached: bool, status: str, error: str = None):
        # We assume the metric_id exists in the DB for executions (if it's a predefined one, 
        # it should be seeded. For MVP, we might skip the FK constraint if it's not seeded yet).
        # We'll skip DB write if it fails FK to prevent breaking the flow.
        try:
            exec_log = MetricExecution(
                metric_id=metric_id, # This might fail FK if not seeded in DB
                execution_time_ms=exec_time_s * 1000,
                was_cached=was_cached,
                status=status,
                errors={"error": error} if error else None
            )
            db.add(exec_log)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Could not log metric execution (likely missing FK): {e}")

business_metrics_service = BusinessMetricsService()
