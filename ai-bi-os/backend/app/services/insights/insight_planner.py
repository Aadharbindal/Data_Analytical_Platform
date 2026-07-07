from sqlalchemy.orm import Session
from typing import Dict, List, Any
from app.models.analytics import AnalyticsRun, AnalyticsBusinessMetric, TrendAnalysis, SegmentAnalysis, VarianceAnalysis

class InsightPlanner:
    """Determines which insight detection algorithms to run based on available analytics data."""
    
    @staticmethod
    def plan(db: Session, run_id: str) -> Dict[str, Any]:
        run = db.query(AnalyticsRun).filter(AnalyticsRun.id == run_id).first()
        if not run:
            raise ValueError("Analytics Run not found")
            
        metrics = db.query(BusinessMetric).filter(BusinessMetric.run_id == run_id).all()
        trends = db.query(TrendAnalysis).filter(TrendAnalysis.run_id == run_id).all()
        segments = db.query(SegmentAnalysis).filter(SegmentAnalysis.run_id == run_id).all()
        variances = db.query(VarianceAnalysis).filter(VarianceAnalysis.run_id == run_id).all()
        
        return {
            "dataset_version_id": run.dataset_version_id,
            "has_metrics": len(metrics) > 0,
            "has_trends": len(trends) > 0,
            "has_segments": len(segments) > 0,
            "has_variances": len(variances) > 0,
            "data": {
                "metrics": metrics,
                "trends": trends,
                "segments": segments,
                "variances": variances
            }
        }
