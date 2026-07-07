import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.eda import (
    EDARun, EDAProfile, EDAColumnProfile, DatasetSummary, 
    DistributionSummary, MissingValueAnalysis, OutlierCandidate, EDAHistory
)

logger = logging.getLogger("EDARepository")

class EDARepository:
    """Handles DB writes for EDA objects."""
    
    def create_run(self, db: Session, dataset_id: str, dataset_version_id: str) -> EDARun:
        run = EDARun(dataset_id=dataset_id, dataset_version_id=dataset_version_id)
        db.add(run)
        db.flush()
        return run
        
    def save_profile(self, db: Session, run_id: str, health_scores: Dict[str, float], warnings: List[str]) -> EDAProfile:
        profile = EDAProfile(
            run_id=run_id,
            completeness_score=health_scores.get("completeness", 0.0),
            consistency_score=health_scores.get("consistency", 0.0),
            usability_score=health_scores.get("usability", 0.0),
            eda_quality_score=health_scores.get("eda_quality", 0.0),
            warnings=warnings
        )
        db.add(profile)
        db.flush()
        return profile
        
    def save_dataset_summary(self, db: Session, profile_id: str, summary_data: Dict[str, Any]) -> DatasetSummary:
        summary = DatasetSummary(
            profile_id=profile_id,
            total_rows=summary_data.get("total_rows", 0),
            total_columns=summary_data.get("total_columns", 0),
            dataset_size_bytes=summary_data.get("dataset_size_bytes", 0),
            memory_usage_bytes=summary_data.get("memory_usage_bytes", 0),
            numeric_columns=summary_data.get("numeric_columns", 0),
            categorical_columns=summary_data.get("categorical_columns", 0),
            date_columns=summary_data.get("date_columns", 0),
            boolean_columns=summary_data.get("boolean_columns", 0),
            text_columns=summary_data.get("text_columns", 0)
        )
        db.add(summary)
        return summary
        
    def log_history(self, db: Session, dataset_version_id: str, action: str, 
                    exec_time: float = None, errors: Dict = None):
        history = EDAHistory(
            dataset_version_id=dataset_version_id,
            action=action,
            execution_time_ms=exec_time,
            errors=errors
        )
        db.add(history)
        db.commit()

eda_repository = EDARepository()
