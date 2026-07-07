import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.correlation import (
    CorrelationRun, CorrelationResult, AssociationResult, 
    CorrelationMatrix, FeatureRelationship, CorrelationHistory
)

logger = logging.getLogger("CorrelationRepository")

class CorrelationRepository:
    """Handles DB writes for Correlation objects."""
    
    def create_run(self, db: Session, dataset_id: str, dataset_version_id: str) -> CorrelationRun:
        run = CorrelationRun(dataset_id=dataset_id, dataset_version_id=dataset_version_id)
        db.add(run)
        db.flush()
        return run
        
    def save_numeric_correlation(self, db: Session, run_id: str, result: Dict[str, Any]):
        corr = CorrelationResult(
            run_id=run_id,
            column_x=result["column_x"],
            column_y=result["column_y"],
            method_used=result["method_used"],
            coefficient=result["coefficient"],
            p_value=result["p_value"],
            sample_size=result["sample_size"],
            is_significant=result["is_significant"],
            strength_classification=result["strength_classification"]
        )
        db.add(corr)
        
    def save_association(self, db: Session, run_id: str, result: Dict[str, Any]):
        assoc = AssociationResult(
            run_id=run_id,
            column_x=result["column_x"],
            column_y=result["column_y"],
            method_used=result["method_used"],
            coefficient=result["coefficient"],
            p_value=result.get("p_value"),
            sample_size=result["sample_size"],
            is_significant=result["is_significant"],
            strength_classification=result["strength_classification"]
        )
        db.add(assoc)
        
    def save_matrix(self, db: Session, run_id: str, matrix_type: str, data: Dict[str, Any]):
        matrix = CorrelationMatrix(
            run_id=run_id,
            matrix_type=matrix_type,
            data=data
        )
        db.add(matrix)
        
    def save_feature_relationship(self, db: Session, run_id: str, rel: Dict[str, Any]):
        feat_rel = FeatureRelationship(
            run_id=run_id,
            source_metric=rel["source_metric"],
            target_metric=rel["target_metric"],
            relationship_type=rel["relationship_type"],
            business_relevance=rel.get("business_relevance"),
            supporting_statistics=rel.get("supporting_statistics")
        )
        db.add(feat_rel)
        
    def log_history(self, db: Session, dataset_version_id: str, action: str, 
                    exec_time: float = None, errors: Dict = None):
        history = CorrelationHistory(
            dataset_version_id=dataset_version_id,
            action=action,
            execution_time_ms=exec_time,
            errors=errors
        )
        db.add(history)
        db.commit()

correlation_repository = CorrelationRepository()
