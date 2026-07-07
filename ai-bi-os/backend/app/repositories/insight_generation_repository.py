from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any

from app.models.insight_generation import (
    InsightGenerationObject, InsightReference, InsightHistory,
    InsightPriority, InsightObjectValidation, InsightMetrics, InsightAudit
)

class InsightGenerationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_insight(self, insight: InsightGenerationObject) -> InsightGenerationObject:
        self.db.add(insight)
        self.db.commit()
        self.db.refresh(insight)
        return insight

    def get_insight(self, insight_id: str) -> Optional[InsightGenerationObject]:
        return self.db.query(InsightGenerationObject).filter(InsightGenerationObject.id == insight_id).first()

    def update_insight(self, insight: InsightGenerationObject) -> InsightGenerationObject:
        self.db.add(insight)
        self.db.commit()
        self.db.refresh(insight)
        return insight

    def list_insights_by_workspace(self, workspace_id: str, limit: int = 50) -> List[InsightGenerationObject]:
        return self.db.query(InsightGenerationObject).filter(
            InsightGenerationObject.workspace_id == workspace_id
        ).order_by(InsightGenerationObject.priority.desc(), InsightGenerationObject.generated_at.desc()).limit(limit).all()
        
    def list_insights_by_dataset(self, dataset_id: str, limit: int = 50) -> List[InsightGenerationObject]:
        return self.db.query(InsightGenerationObject).filter(
            InsightGenerationObject.dataset_id == dataset_id
        ).order_by(InsightGenerationObject.priority.desc(), InsightGenerationObject.generated_at.desc()).limit(limit).all()

    def count_insights(self, workspace_id: str) -> int:
        return self.db.query(func.count(InsightGenerationObject.id)).filter(InsightGenerationObject.workspace_id == workspace_id).scalar() or 0

    def add_reference(self, reference: InsightReference):
        self.db.add(reference)
        self.db.commit()

    def add_history(self, history: InsightHistory):
        self.db.add(history)
        self.db.commit()

    def add_priority(self, priority: InsightPriority):
        self.db.add(priority)
        self.db.commit()

    def add_validation(self, validation: InsightObjectValidation):
        self.db.add(validation)
        self.db.commit()

    def log_metrics(self, metric: InsightMetrics):
        self.db.add(metric)
        self.db.commit()
