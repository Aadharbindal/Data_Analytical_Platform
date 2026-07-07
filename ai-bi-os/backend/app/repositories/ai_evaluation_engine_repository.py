from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.models.ai_evaluation_engine import (
    EvaluationObject, EvaluationMetric, Leaderboard, RegressionReport, EvaluationHistory
)

class AIEvaluationEngineRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_evaluation(self, eval_obj: EvaluationObject) -> EvaluationObject:
        self.db.add(eval_obj)
        self.db.commit()
        self.db.refresh(eval_obj)
        return eval_obj

    def get_evaluation(self, eval_id: str) -> Optional[EvaluationObject]:
        return self.db.query(EvaluationObject).filter(EvaluationObject.id == eval_id).first()

    def list_evaluations(self, limit: int = 100) -> List[EvaluationObject]:
        return self.db.query(EvaluationObject).order_by(EvaluationObject.timestamp.desc()).limit(limit).all()

    def add_metric(self, metric: EvaluationMetric):
        self.db.add(metric)
        self.db.commit()

    def update_leaderboard(self, entry: Leaderboard):
        # Very simplified upsert for mock
        existing = self.db.query(Leaderboard).filter(
            Leaderboard.workspace_id == entry.workspace_id,
            Leaderboard.category == entry.category,
            Leaderboard.entity_name == entry.entity_name
        ).first()
        
        if existing:
            existing.aggregated_score = entry.aggregated_score
            existing.overall_rank = entry.overall_rank
            self.db.commit()
        else:
            self.db.add(entry)
            self.db.commit()

    def list_leaderboard(self, category: str, workspace_id: str) -> List[Leaderboard]:
        return self.db.query(Leaderboard).filter(
            Leaderboard.workspace_id == workspace_id,
            Leaderboard.category == category
        ).order_by(Leaderboard.overall_rank.asc()).all()

    def add_regression(self, regression: RegressionReport):
        self.db.add(regression)
        self.db.commit()
        
    def list_regressions(self, workspace_id: str) -> List[RegressionReport]:
        return self.db.query(RegressionReport).filter(
            RegressionReport.workspace_id == workspace_id
        ).order_by(RegressionReport.timestamp.desc()).all()

    def add_history(self, history: EvaluationHistory):
        self.db.add(history)
        self.db.commit()
