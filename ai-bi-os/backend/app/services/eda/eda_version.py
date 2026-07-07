import logging
from sqlalchemy.orm import Session
from app.models.eda import EDARun

logger = logging.getLogger("EDAVersionManager")

class EDAVersionManager:
    """Manages EDA runs against specific dataset versions."""
    
    def get_latest_run_for_version(self, db: Session, dataset_version_id: str) -> EDARun:
        """Retrieves the most recent successful EDA run for a version."""
        return db.query(EDARun).filter(
            EDARun.dataset_version_id == dataset_version_id,
            EDARun.status == "COMPLETED"
        ).order_by(EDARun.generated_at.desc()).first()

eda_version_manager = EDAVersionManager()
