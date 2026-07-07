from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any

from app.models.recommendation_intelligence import (
    RecommendationObject, RecommendationReference, RecommendationIntelligenceHistory,
    RecommendationPriority, RecommendationValidation, RecommendationScenario,
    RecommendationActionPlan, RecommendationMetrics, RecommendationAudit
)

class RecommendationIntelligenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_recommendation(self, recommendation: RecommendationObject) -> RecommendationObject:
        self.db.add(recommendation)
        self.db.commit()
        self.db.refresh(recommendation)
        return recommendation

    def get_recommendation(self, recommendation_id: str) -> Optional[RecommendationObject]:
        return self.db.query(RecommendationObject).filter(RecommendationObject.id == recommendation_id).first()

    def update_recommendation(self, recommendation: RecommendationObject) -> RecommendationObject:
        self.db.add(recommendation)
        self.db.commit()
        self.db.refresh(recommendation)
        return recommendation

    def list_recommendations(self, workspace_id: str, limit: int = 50) -> List[RecommendationObject]:
        return self.db.query(RecommendationObject).filter(
            RecommendationObject.workspace_id == workspace_id,
            RecommendationObject.status == "OPEN"
        ).order_by(RecommendationObject.priority.asc(), RecommendationObject.generated_at.desc()).limit(limit).all()

    def count_recommendations(self, workspace_id: str) -> int:
        return self.db.query(func.count(RecommendationObject.id)).filter(RecommendationObject.workspace_id == workspace_id).scalar() or 0

    def add_reference(self, reference: RecommendationReference):
        self.db.add(reference)
        self.db.commit()

    def add_history(self, history: RecommendationIntelligenceHistory):
        self.db.add(history)
        self.db.commit()

    def add_priority(self, priority: RecommendationPriority):
        self.db.add(priority)
        self.db.commit()

    def add_validation(self, validation: RecommendationValidation):
        self.db.add(validation)
        self.db.commit()
        
    def add_scenario(self, scenario: RecommendationScenario):
        self.db.add(scenario)
        self.db.commit()
        
    def add_action_plan(self, action_plan: RecommendationActionPlan):
        self.db.add(action_plan)
        self.db.commit()

    def log_metrics(self, metric: RecommendationMetrics):
        self.db.add(metric)
        self.db.commit()
