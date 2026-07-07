from typing import List
from sqlalchemy.orm import Session
from app.models.rule import Decision

class RecommendationPlanner:
    """Ingests Decisions and determines applicable recommendation templates."""
    
    @staticmethod
    def plan(db: Session, dataset_version_id: str) -> List[Decision]:
        # Fetch all unresolved decisions for this dataset version
        decisions = db.query(Decision).filter(
            Decision.dataset_version_id == dataset_version_id
            # In a full app, we might filter out decisions that already have a recommendation
        ).all()
        return decisions
