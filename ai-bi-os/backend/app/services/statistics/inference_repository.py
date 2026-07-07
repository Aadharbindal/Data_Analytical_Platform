import logging
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.models.statistics import (
    StatisticalRun, HypothesisTest, ConfidenceInterval, StatDistributionProfile,
    SamplingProfile, InferenceResult, ProbabilityResult, InferenceHistory
)

logger = logging.getLogger("InferenceRepository")

class InferenceRepository:
    """DB operations for Statistics."""
    
    def create_run(self, db: Session, dataset_id: str, dataset_version_id: str) -> StatisticalRun:
        run = StatisticalRun(dataset_id=dataset_id, dataset_version_id=dataset_version_id)
        db.add(run)
        db.flush()
        return run
        
    def save_hypothesis_test(self, db: Session, run_id: str, data: Dict[str, Any]):
        h = HypothesisTest(run_id=run_id, **data)
        db.add(h)
        
    def save_confidence_interval(self, db: Session, run_id: str, data: Dict[str, Any]):
        c = ConfidenceInterval(run_id=run_id, **data)
        db.add(c)
        
    def save_distribution_profile(self, db: Session, run_id: str, data: Dict[str, Any]):
        d = StatDistributionProfile(run_id=run_id, **data)
        db.add(d)
        
    def save_sampling_profile(self, db: Session, run_id: str, data: Dict[str, Any]):
        s = SamplingProfile(run_id=run_id, **data)
        db.add(s)
        
    def save_probability_result(self, db: Session, run_id: str, data: Dict[str, Any]):
        p = ProbabilityResult(run_id=run_id, **data)
        db.add(p)
        
    def save_inference_result(self, db: Session, run_id: str, data: Dict[str, Any]):
        i = InferenceResult(run_id=run_id, **data)
        db.add(i)
        
    def log_history(self, db: Session, dataset_version_id: str, action: str, exec_time: float = None):
        history = InferenceHistory(
            dataset_version_id=dataset_version_id,
            action=action,
            execution_time_ms=exec_time
        )
        db.add(history)
        db.commit()

inference_repository = InferenceRepository()
