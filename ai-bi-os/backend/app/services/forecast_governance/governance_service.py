from sqlalchemy.orm import Session
from app.models.forecast_governance import ModelGovernance
from app.services.forecast_governance.evaluation_service import evaluation_service
from app.services.forecast_governance.monitor import forecast_monitor
from app.services.forecast_governance.drift_detector import drift_detector
from app.services.forecast_governance.lifecycle_manager import lifecycle_manager
from app.services.forecast_governance.benchmark_engine import benchmark_engine

class GovernanceService:
    def get_or_create_governance(self, db: Session, model_id: str, name: str, forecast_id: str = None) -> ModelGovernance:
        gov = db.query(ModelGovernance).filter(ModelGovernance.model_id == model_id).first()
        if not gov:
            gov = ModelGovernance(model_id=model_id, name=name, forecast_id=forecast_id)
            db.add(gov)
            db.commit()
            db.refresh(gov)
            # Init lifecycle
            lifecycle_manager.transition_state(db, model_id, "Development", "System", "Initial creation")
        return gov

    def compute_quality_scores(self, db: Session, model_id: str) -> dict:
        gov = db.query(ModelGovernance).filter(ModelGovernance.model_id == model_id).first()
        if not gov:
            return {}
            
        # Simplistic scoring logic based on existence of metrics
        evals = gov.evaluations
        drifts = gov.drifts
        
        quality_score = 100.0
        if evals:
            latest_eval = sorted(evals, key=lambda x: x.timestamp)[-1]
            if latest_eval.mape and latest_eval.mape > 0.2:
                quality_score -= 20
        
        trust_score = 100.0
        if drifts:
            latest_drift = sorted(drifts, key=lambda x: x.timestamp)[-1]
            if latest_drift.prediction_drift_detected:
                trust_score -= 30
                
        gov.quality_score = quality_score
        gov.trust_score = trust_score
        db.commit()
        db.refresh(gov)
        
        return {"quality_score": quality_score, "trust_score": trust_score}

governance_service = GovernanceService()
