from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.services.query.query_orchestrator import QueryOrchestrator
from app.models.analytics import CorrelationAnalysis

class CorrelationEngine:
    """Calculates statistical correlations (e.g. Pearson) between numerical columns."""
    
    @staticmethod
    def calculate_correlations(db: Session, dataset_version_id: str, workspace_id: str, semantic_metadata: List[Dict[str, Any]], run_id: str) -> List[CorrelationAnalysis]:
        correlations = []
        
        num_cols = [c["original_header"] for c in semantic_metadata if c.get("inferred_semantic_type") in ["INTEGER", "FLOAT"]]
        
        if len(num_cols) >= 2:
            col_x = num_cols[0]
            col_y = num_cols[1]
            
            # DuckDB natively supports corr(x, y)
            sql = f'SELECT corr("{col_x}", "{col_y}") as pearson_r FROM dataset'
            
            try:
                res = QueryOrchestrator.execute_query(db, sql, dataset_version_id, workspace_id)
                if res and res["rows"] and res["rows"][0].get("pearson_r") is not None:
                    r_val = float(res["rows"][0]["pearson_r"])
                    corr = CorrelationAnalysis(
                        run_id=run_id,
                        column_x=col_x,
                        column_y=col_y,
                        correlation_coefficient=r_val,
                        method="PEARSON"
                    )
                    correlations.append(corr)
            except Exception:
                pass
                
        return correlations
