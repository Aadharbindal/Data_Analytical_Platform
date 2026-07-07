from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.services.query.query_orchestrator import QueryOrchestrator
from app.models.analytics import SegmentAnalysis

class SegmentationEngine:
    """Groups data by high-cardinality categorical dimensions."""
    
    @staticmethod
    def calculate_segments(db: Session, dataset_version_id: str, workspace_id: str, semantic_metadata: List[Dict[str, Any]], run_id: str) -> List[SegmentAnalysis]:
        segments = []
        
        cat_cols = [c["original_header"] for c in semantic_metadata if c.get("inferred_semantic_type") == "STRING"]
        num_cols = [c["original_header"] for c in semantic_metadata if c.get("inferred_semantic_type") in ["INTEGER", "FLOAT"]]
        
        if not cat_cols or not num_cols:
            return segments
            
        dim = cat_cols[0]
        metric = num_cols[0]
        
        # Execute Group By
        sql = f'SELECT "{dim}" as dim_val, SUM("{metric}") as metric_val FROM dataset GROUP BY "{dim}" ORDER BY metric_val DESC LIMIT 5'
        
        try:
            res = QueryOrchestrator.execute_query(db, sql, dataset_version_id, workspace_id)
            if res and res["rows"]:
                total = sum([float(r["metric_val"]) for r in res["rows"] if r.get("metric_val") is not None])
                
                for r in res["rows"]:
                    if r.get("dim_val") and r.get("metric_val") is not None:
                        val = float(r["metric_val"])
                        pct = (val / total * 100) if total > 0 else 0
                        seg = SegmentAnalysis(
                            run_id=run_id,
                            dimension=dim,
                            segment_value=str(r["dim_val"]),
                            metric_name=metric,
                            metric_value=val,
                            percentage_of_total=pct
                        )
                        segments.append(seg)
        except Exception:
            pass
            
        return segments
