import time
from typing import Dict, Any, Tuple, List
from sqlalchemy.orm import Session

from app.models.ai_validation_engine import (
    ValidationObject, ValidationResult, ValidationHistory, ValidationMetrics
)
from app.repositories.ai_validation_engine_repository import AIValidationEngineRepository
from app.services.ai_validation_engine.validators import (
    FactChecker, EvidenceValidator, NumericalValidator, 
    PolicyValidator, SchemaValidator, ConfidenceValidator
)

class ValidationPipeline:
    """Orchestrates the validation sequence."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = AIValidationEngineRepository(db)
        self.validators = [
            ("SchemaValidator", SchemaValidator()),
            ("FactChecker", FactChecker()),
            ("NumericalValidator", NumericalValidator()),
            ("EvidenceValidator", EvidenceValidator()),
            ("PolicyValidator", PolicyValidator()),
            ("ConfidenceValidator", ConfidenceValidator())
        ]

    def validate(self, workspace_id: str, object_id: str, object_type: str, payload: Dict[str, Any]) -> ValidationObject:
        start_time = time.time()
        
        val_obj = ValidationObject(
            workspace_id=workspace_id,
            object_id=object_id,
            object_type=object_type,
            confidence_score=payload.get("confidence", 0.9),
            evidence_score=0.8,
            policy_score=1.0,
            validation_status="PENDING"
        )
        val_obj = self.repository.create_validation(val_obj)
        
        self.repository.add_history(ValidationHistory(validation_id=val_obj.id, event="VALIDATION_STARTED"))
        
        final_status = "APPROVED"
        warnings = []
        errors = []
        
        for name, validator in self.validators:
            status, msg = validator.validate(payload)
            
            result = ValidationResult(
                validation_id=val_obj.id,
                validator_name=name,
                status=status,
                message=msg
            )
            self.repository.add_result(result)
            
            if status == "FAIL":
                final_status = "REJECTED"
                errors.append(msg)
            elif status == "WARN":
                if final_status != "REJECTED":
                    final_status = "APPROVED" # Warn doesn't reject, but notes it
                warnings.append(msg)
                
        val_obj.validation_status = final_status
        val_obj.warnings = warnings
        val_obj.errors = errors
        
        if final_status == "APPROVED":
            from datetime import datetime
            val_obj.approved_at = datetime.utcnow()
            
        self.repository.update_validation(val_obj)
        self.repository.add_history(ValidationHistory(validation_id=val_obj.id, event=final_status))
        
        latency = int((time.time() - start_time) * 1000)
        self.repository.log_metrics(ValidationMetrics(
            workspace_id=workspace_id,
            validation_time_ms=latency,
            final_status=final_status,
            object_type=object_type
        ))
        
        return val_obj
