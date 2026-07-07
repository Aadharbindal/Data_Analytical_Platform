import time
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.dataset import DatasetVersion, Dataset
from app.models.analytics import AnalyticsRun
from app.services.schema.schema_registry import SchemaRegistryService
from app.services.analytics.metric_engine import MetricEngine
from app.services.analytics.trend_engine import TrendEngine
from app.services.analytics.segmentation_engine import SegmentationEngine
from app.services.analytics.variance_engine import VarianceEngine
from app.services.analytics.correlation_engine import CorrelationEngine
from app.services.analytics.insight_builder import InsightBuilder

class AnalyticsOrchestrator:
    """Coordinates the deterministic calculation of all analytics."""
    
    @staticmethod
    def run_analytics(db: Session, dataset_version_id: str) -> str:
        version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
        if not version:
            raise ValueError("Dataset version not found")
            
        dataset = db.query(Dataset).filter(Dataset.id == version.dataset_id).first()
            
        run = AnalyticsRun(dataset_version_id=dataset_version_id, status="RUNNING")
        db.add(run)
        db.commit()
        
        start_time = time.perf_counter()
        
        try:
            # Get Semantic schema info to guide analytics
            schema_registry = SchemaRegistryService(db)
            schema = schema_registry.get_schema_for_dataset(dataset.id)
            if not schema:
                raise ValueError("Schema not found, cannot perform analytics")
                
            semantic_metadata = [{"original_header": c.original_header, "inferred_semantic_type": c.inferred_semantic_type} for c in schema.columns]
            
            # 1. Metrics
            metrics = MetricEngine.calculate_metrics(db, dataset_version_id, dataset.workspace_id, semantic_metadata, run.id)
            db.add_all(metrics)
            
            # 2. Trends
            trends = TrendEngine.calculate_trends(db, dataset_version_id, dataset.workspace_id, semantic_metadata, run.id)
            db.add_all(trends)
            
            # 3. Segments
            segments = SegmentationEngine.calculate_segments(db, dataset_version_id, dataset.workspace_id, semantic_metadata, run.id)
            db.add_all(segments)
            
            # 4. Variances
            variances = VarianceEngine.calculate_variances(db, dataset_version_id, dataset.workspace_id, semantic_metadata, run.id)
            db.add_all(variances)
            
            # 5. Correlations
            correlations = CorrelationEngine.calculate_correlations(db, dataset_version_id, dataset.workspace_id, semantic_metadata, run.id)
            db.add_all(correlations)
            
            # 6. Build Insights
            insights = InsightBuilder.build_insights(run.id, metrics, trends, segments, variances, correlations)
            db.add_all(insights)
            
            end_time = time.perf_counter()
            
            run.status = "COMPLETED"
            run.execution_time_ms = (end_time - start_time) * 1000
            run.metrics_generated = len(metrics) + len(trends) + len(segments) + len(variances) + len(correlations) + len(insights)
            run.completed_at = datetime.utcnow()
            
            db.commit()
            return run.id
            
        except Exception as e:
            run.status = "FAILED"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            db.commit()
            raise e
