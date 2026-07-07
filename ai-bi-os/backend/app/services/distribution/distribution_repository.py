import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.distribution import (
    DistributionRun, DistributionProfile, DistributionFit, DistributionParameter,
    GoodnessOfFitResult, DensityProfile, TailAnalysis, DistributionHistory
)

logger = logging.getLogger("DistributionRepository")

class DistributionRepository:
    """DB operations for Distribution Engine."""
    
    def create_run(self, db: Session, dataset_id: str, dataset_version_id: str) -> DistributionRun:
        run = DistributionRun(dataset_id=dataset_id, dataset_version_id=dataset_version_id)
        db.add(run)
        db.flush()
        return run
        
    def save_profile(self, db: Session, run_id: str, profile_data: Dict[str, Any]) -> DistributionProfile:
        p = DistributionProfile(run_id=run_id, **profile_data)
        db.add(p)
        db.flush()
        return p
        
    def save_fit(self, db: Session, profile_id: str, fit_data: Dict[str, Any]):
        f = DistributionFit(
            profile_id=profile_id,
            distribution_type=fit_data["distribution_type"],
            is_best_fit=fit_data.get("is_best_fit", False),
            log_likelihood=fit_data.get("log_likelihood"),
            aic=fit_data.get("aic"),
            bic=fit_data.get("bic")
        )
        db.add(f)
        db.flush()
        
        for param in fit_data.get("parameters", []):
            p = DistributionParameter(fit_id=f.id, parameter_name=param["name"], parameter_value=param["value"])
            db.add(p)
            
        for gof in fit_data.get("gof_results", []):
            g = GoodnessOfFitResult(fit_id=f.id, **gof)
            db.add(g)
            
    def save_density(self, db: Session, profile_id: str, density_data: Dict[str, Any]):
        d = DensityProfile(profile_id=profile_id, **density_data)
        db.add(d)
        
    def save_tail_analysis(self, db: Session, profile_id: str, tail_data: Dict[str, Any]):
        t = TailAnalysis(profile_id=profile_id, **tail_data)
        db.add(t)
        
    def log_history(self, db: Session, run_id: str, action: str):
        h = DistributionHistory(run_id=run_id, action=action)
        db.add(h)
        db.commit()

distribution_repository = DistributionRepository()
