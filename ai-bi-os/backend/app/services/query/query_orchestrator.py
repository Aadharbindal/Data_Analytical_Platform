from sqlalchemy.orm import Session
from typing import Dict, Any, List
from fastapi import HTTPException
import os

from app.services.query.duckdb_engine import DuckDBEngine
from app.services.query.query_validator import QueryValidator
from app.services.query.execution_profiler import ExecutionProfiler
from app.services.query.query_cache_manager import QueryCacheManager
from app.models.dataset import DatasetVersion
from app.models.query import QueryHistory

class QueryOrchestrator:
    """Coordinates validation, caching, profiling, and execution of SQL."""
    
    @staticmethod
    def execute_query(db: Session, sql: str, dataset_version_id: str, workspace_id: str, skip_cache: bool = False) -> Dict[str, Any]:
        # 1. Validate Query Security
        QueryValidator.validate(sql)
        
        # 2. Check Cache
        if not skip_cache:
            cached_res = QueryCacheManager.get_cached_result(db, sql, dataset_version_id)
            if cached_res:
                # Log to history as a cache hit
                hist = QueryHistory(
                    workspace_id=workspace_id,
                    query_sql=sql,
                    status="SUCCESS",
                    cache_hit=True,
                    rows_returned=len(cached_res.get("rows", []))
                )
                db.add(hist)
                db.commit()
                
                cached_res["metadata"] = {"cache_hit": True, "execution_time_ms": 0}
                return cached_res
                
        # 3. Setup Execution Environment
        version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
        if not version:
            raise HTTPException(status_code=404, detail="Dataset version not found")
            
        file_path = version.file_path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Underlying data file not found")
            
        engine = DuckDBEngine()
        profiler = ExecutionProfiler()
        
        try:
            # Register the dataset view. Assuming view name is "dataset" for simplicity.
            # In a real environment, you'd map the logical table names used in the SQL to the specific file paths.
            format = "parquet" if file_path.endswith(".parquet") else "csv"
            
            # Extract the table name from the FROM clause for registering (simplistic approach for demo)
            # A more robust approach uses an AST parser to find all table references and map them to datasets in the workspace.
            # We will default register it as "dataset" and assume the query targets "FROM dataset".
            engine.register_dataset("dataset", file_path, format=format)
            
            # 4. Profile and Execute
            with profiler.profile() as stats:
                result = engine.execute(sql)
                stats["rows_returned"] = len(result["rows"])
                stats["rows_scanned"] = len(result["rows"]) # Approximation for DuckDB unless we parse plan
                
            # 5. Build Result
            final_response = {
                "schema": result["schema"],
                "rows": result["rows"],
                "metadata": {
                    "cache_hit": False,
                    "execution_time_ms": stats["execution_time_ms"],
                    "rows_returned": stats["rows_returned"]
                }
            }
            
            # 6. Cache Result
            QueryCacheManager.set_cached_result(db, sql, dataset_version_id, final_response)
            
            # 7. Log History
            hist = QueryHistory(
                workspace_id=workspace_id,
                dataset_id=version.dataset_id,
                query_sql=sql,
                status="SUCCESS",
                execution_time_ms=stats["execution_time_ms"],
                rows_returned=stats["rows_returned"],
                cache_hit=False
            )
            db.add(hist)
            db.commit()
            
            return final_response
            
        except Exception as e:
            # Log Failure
            hist = QueryHistory(
                workspace_id=workspace_id,
                dataset_id=version.dataset_id,
                query_sql=sql,
                status="FAILED",
                error_message=str(e)
            )
            db.add(hist)
            db.commit()
            raise e
        finally:
            engine.close()
            
    @staticmethod
    def explain_query(db: Session, sql: str, dataset_version_id: str) -> str:
        QueryValidator.validate(sql)
        version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
        if not version or not os.path.exists(version.file_path):
            raise HTTPException(status_code=404, detail="Dataset not found")
            
        engine = DuckDBEngine()
        try:
            format = "parquet" if version.file_path.endswith(".parquet") else "csv"
            engine.register_dataset("dataset", version.file_path, format=format)
            return engine.explain(sql)
        finally:
            engine.close()
