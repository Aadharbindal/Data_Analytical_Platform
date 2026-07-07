import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.trend import (
    TrendRun, TrendProfile, TrendResult, ChangePoint,
    TrendSummary, TrendValidation, TrendHistory
)

logger = logging.getLogger("TrendRepository")

class TrendRepository:
    """DB operations for Trend Engine."""
    
    def create_run(self, db: Session, dataset_id: str, dataset_version_id: str) -> TrendRun:
        run = TrendRun(dataset_id=dataset_id, dataset_version_id=dataset_version_id)
        db.add(run)
        db.flush()
        return run
        
    def save_profile(self, db: Session, run_id: str, profile_data: Dict[str, Any]) -> TrendProfile:
        p = TrendProfile(run_id=run_id, **profile_data)
        db.add(p)
        db.flush()
        return p
        
    def save_segment(self, db: Session, profile_id: str, segment_data: Dict[str, Any]):
        s = TrendResult(profile_id=profile_id, **segment_data)
        db.add(s)
        
    def save_change_point(self, db: Session, profile_id: str, cp_data: Dict[str, Any]):
        cp = ChangePoint(profile_id=profile_id, **cp_data)
        db.add(cp)
        
    def save_summary(self, db: Session, run_id: str, summary_data: Dict[str, Any]):
        s = TrendSummary(run_id=run_id, **summary_data)
        db.add(s)
        
    def log_validation(self, db: Session, profile_id: str, val_data: Dict[str, Any]):
        v = TrendValidation(profile_id=profile_id, **val_data)
        db.add(v)
        
    def log_history(self, db: Session, run_id: str, action: str):
        h = TrendHistory(run_id=run_id, action=action)
        db.add(h)
        db.commit()

trend_repository = TrendRepository()
