import logging
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.models.validation import (
    ValidationRun, ValidationResult, ConfidenceScore, ReliabilityScore, ValidationHistory
)

logger = logging.getLogger("ValidationRepository")

class ValidationRepository:
    """DB operations for Validation Engine."""
    
    def create_run(self, db: Session, target_id: str, target_type: str) -> ValidationRun:
        run = ValidationRun(target_object_id=target_id, target_object_type=target_type)
        db.add(run)
        db.flush()
        return run
        
    def save_result(self, db: Session, run_id: str, status: str, errors: list, warnings: list):
        res = ValidationResult(
            run_id=run_id, 
            validation_status=status,
            errors=errors,
            warnings=warnings,
            policy_version="1.0",
            validator_version="1.0"
        )
        db.add(res)
        
    def save_confidence(self, db: Session, run_id: str, confidence: Dict[str, Any]):
        c = ConfidenceScore(run_id=run_id, **confidence)
        db.add(c)
        
    def save_reliability(self, db: Session, run_id: str, reliability: Dict[str, Any]):
        r = ReliabilityScore(run_id=run_id, **reliability)
        db.add(r)
        
    def log_history(self, db: Session, run_id: str, action: str):
        h = ValidationHistory(run_id=run_id, action=action)
        db.add(h)
        db.commit()

validation_repository = ValidationRepository()
