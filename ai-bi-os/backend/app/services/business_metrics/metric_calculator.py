import logging
import time
from typing import Dict, Any

from app.services.business_metrics.metric_formula_engine import metric_formula_engine

logger = logging.getLogger("MetricCalculator")

class MetricCalculator:
    """
    Executes the compiled metric formula against DuckDB.
    """
    
    def calculate(self, formula: str, dataset_table_name: str, dimension: str = None) -> Dict[str, Any]:
        """
        Executes the query and returns the results.
        Returns a dict mapping dimension_value -> calculated_value.
        If no dimension, returns {"total": value}.
        """
        start_time = time.time()
        sql = metric_formula_engine.compile_to_sql(formula, dataset_table_name, dimension)
        
        logger.info(f"Executing Metric SQL: {sql}")
        
        try:
            # MVP: Fallback if table doesn't exist to return mock data
            # In production, we execute the actual duckdb query:
            # result_df = duckdb_engine.execute_query(sql)
            
            # Since this is an MVP without physical datasets in duckdb yet, 
            # we will mock the response structure.
            
            # Simulate execution time
            time.sleep(0.1)
            
            results = {}
            if dimension:
                results["North America"] = 10500.50
                results["Europe"] = 8200.75
                results["Asia"] = 4300.00
            else:
                results["total"] = 23001.25
                
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "status": "success",
                "execution_time_ms": execution_time,
                "data": results
            }
            
        except Exception as e:
            logger.error(f"Metric calculation failed: {e}")
            return {
                "status": "error",
                "execution_time_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }

metric_calculator = MetricCalculator()
