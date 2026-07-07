from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.models.ai_validation_engine import (
    ValidationObject, ValidationResult, ValidationHistory, ValidationMetrics
)

class AIValidationEngineRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_validation(self, validation: ValidationObject) -> ValidationObject:
        self.db.add(validation)
        self.db.commit()
        self.db.refresh(validation)
        return validation

    def get_validation(self, validation_id: str) -> Optional[ValidationObject]:
        return self.db.query(ValidationObject).filter(ValidationObject.id == validation_id).first()

    def update_validation(self, validation: ValidationObject) -> ValidationObject:
        self.db.add(validation)
        self.db.commit()
        self.db.refresh(validation)
        return validation

    def list_validations(self, limit: int = 100) -> List[ValidationObject]:
        return self.db.query(ValidationObject).order_by(ValidationObject.created_at.desc()).limit(limit).all()

    def add_result(self, result: ValidationResult):
        self.db.add(result)
        self.db.commit()

    def add_history(self, history: ValidationHistory):
        self.db.add(history)
        self.db.commit()

    def log_metrics(self, metric: ValidationMetrics):
        self.db.add(metric)
        self.db.commit()

    def get_statistics(self) -> dict:
        total = self.db.query(func.count(ValidationObject.id)).scalar() or 0
        approved = self.db.query(func.count(ValidationObject.id)).filter(ValidationObject.validation_status == "APPROVED").scalar() or 0
        rejected = self.db.query(func.count(ValidationObject.id)).filter(ValidationObject.validation_status == "REJECTED").scalar() or 0
        
        avg_conf = self.db.query(func.avg(ValidationObject.confidence_score)).scalar() or 0.0

        return {
            "total_validated": total,
            "approval_rate": (approved / total * 100) if total > 0 else 0.0,
            "rejection_rate": (rejected / total * 100) if total > 0 else 0.0,
            "avg_confidence": float(avg_conf)
        }
