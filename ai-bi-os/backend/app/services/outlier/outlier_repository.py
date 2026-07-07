import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.outlier import (
    OutlierRun, OutlierResult, OutlierSummary,
    ExtremeValue, OutlierHistory, OutlierValidation
)

logger = logging.getLogger("OutlierRepository")

class OutlierRepository:
    """DB operations for Outlier Engine."""
    
    def create_run(self, db: Session, dataset_id: str, dataset_version_id: str) -> OutlierRun:
        run = OutlierRun(dataset_id=dataset_id, dataset_version_id=dataset_version_id)
        db.add(run)
        db.flush()
        return run
        
    def save_outlier(self, db: Session, run_id: str, col_name: str, outlier_data: Dict[str, Any]):
        o = OutlierResult(
            run_id=run_id,
            column_name=col_name,
            **outlier_data
        )
        db.add(o)
        
    def save_summary(self, db: Session, run_id: str, summary_data: Dict[str, Any]):
        s = OutlierSummary(run_id=run_id, **summary_data)
        db.add(s)
        
    def save_extreme(self, db: Session, run_id: str, col_name: str, extreme_data: Dict[str, Any]):
        e = ExtremeValue(run_id=run_id, column_name=col_name, **extreme_data)
        db.add(e)
        
    def log_validation(self, db: Session, run_id: str, col_name: str, check_name: str, passed: bool, reason: str = None):
        v = OutlierValidation(run_id=run_id, column_name=col_name, check_name=check_name, passed=passed, reason=reason)
        db.add(v)
        
    def log_history(self, db: Session, run_id: str, action: str):
        h = OutlierHistory(run_id=run_id, action=action)
        db.add(h)
        db.commit()

outlier_repository = OutlierRepository()
