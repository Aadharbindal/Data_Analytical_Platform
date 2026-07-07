import logging
from sqlalchemy.orm import Session
from app.models.correlation import CorrelationRun

logger = logging.getLogger("CorrelationVersionManager")

class CorrelationVersionManager:
    """Manages correlation runs against specific dataset versions."""
    
    def get_latest_run_for_version(self, db: Session, dataset_version_id: str) -> CorrelationRun:
        """Retrieves the most recent successful correlation run for a version."""
        return db.query(CorrelationRun).filter(
            CorrelationRun.dataset_version_id == dataset_version_id,
            CorrelationRun.status == "COMPLETED"
        ).order_by(CorrelationRun.generated_at.desc()).first()

correlation_version_manager = CorrelationVersionManager()
