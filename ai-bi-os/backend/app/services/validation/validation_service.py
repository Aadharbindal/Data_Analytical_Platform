import logging
import time
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.services.validation.validation_registry import validation_registry
from app.services.validation.quality_assessor import quality_assessor
from app.services.validation.validation_rules_engine import validation_rules_engine
from app.services.validation.validation_policy_engine import validation_policy_engine
from app.services.validation.confidence_engine import confidence_engine
from app.services.validation.reliability_engine import reliability_engine
from app.services.validation.validation_repository import validation_repository

logger = logging.getLogger("ValidationService")

class ValidationService:
    """Main orchestrator for Validation Engine."""
    
    def validate_object(self, db: Session, target_object_id: str, target_object_type: str, 
                        metadata: Dict[str, Any], rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        start_time = time.time()
        logger.info(f"Starting Validation for {target_object_type} {target_object_id}")
        
        if not validation_registry.is_supported(target_object_type):
            raise ValueError(f"Target Type {target_object_type} is not supported.")
            
        run = validation_repository.create_run(db, target_object_id, target_object_type)
        run.status = "IN_PROGRESS"
        validation_repository.log_history(db, run.id, "STARTED")
        
        try:
            # 1. Assess Quality
            metrics = quality_assessor.assess_metrics(target_object_type, metadata)
            
            # 2. Evaluate Rules
            rule_results = validation_rules_engine.evaluate_rules(metrics, rules)
            
            # 3. Enforce Policies
            status, errors, warnings = validation_policy_engine.enforce_policy(rule_results)
            
            # 4. Generate Confidence & Reliability
            confidence = confidence_engine.calculate_confidence(target_object_type, metrics)
            reliability = reliability_engine.assess_reliability(confidence)
            
            # 5. Save Results
            validation_repository.save_result(db, run.id, status, errors, warnings)
            validation_repository.save_confidence(db, run.id, confidence)
            validation_repository.save_reliability(db, run.id, reliability)
            
            run.status = "COMPLETED"
            run.execution_time_ms = (time.time() - start_time) * 1000
            
            validation_repository.log_history(db, run.id, "COMPLETED")
            db.commit()
            
            return {
                "validation_id": run.id,
                "status": status,
                "confidence_score": confidence["overall_confidence"],
                "reliability_score": reliability["reliability_score"],
                "errors": errors,
                "warnings": warnings,
                "execution_time_ms": run.execution_time_ms
            }
            
        except Exception as e:
            run.status = "FAILED"
            db.commit()
            validation_repository.log_history(db, run.id, "FAILED")
            logger.error(f"Validation failed: {e}")
            raise e

validation_service = ValidationService()
