import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.timeseries import (
    TimeSeriesRun, TimeSeriesProfile, FrequencyProfile, WindowCalculation,
    GapAnalysis, TemporalValidation, TimeSeriesHistory
)

logger = logging.getLogger("TimeSeriesRepository")

class TimeSeriesRepository:
    """DB operations for TimeSeries Engine."""
    
    def create_run(self, db: Session, dataset_id: str, dataset_version_id: str) -> TimeSeriesRun:
        run = TimeSeriesRun(dataset_id=dataset_id, dataset_version_id=dataset_version_id)
        db.add(run)
        db.flush()
        return run
        
    def save_profile(self, db: Session, run_id: str, profile_data: Dict[str, Any]) -> TimeSeriesProfile:
        p = TimeSeriesProfile(run_id=run_id, **profile_data)
        db.add(p)
        db.flush()
        return p
        
    def save_frequency(self, db: Session, profile_id: str, freq_data: Dict[str, Any]):
        f = FrequencyProfile(profile_id=profile_id, **freq_data)
        db.add(f)
        
    def save_gaps(self, db: Session, profile_id: str, gap_data: Dict[str, Any]):
        g = GapAnalysis(profile_id=profile_id, **gap_data)
        db.add(g)
        
    def save_window(self, db: Session, profile_id: str, window_data: Dict[str, Any]):
        w = WindowCalculation(profile_id=profile_id, **window_data)
        db.add(w)
        
    def log_validation(self, db: Session, profile_id: str, val_data: Dict[str, Any]):
        v = TemporalValidation(profile_id=profile_id, **val_data)
        db.add(v)
        
    def log_history(self, db: Session, run_id: str, action: str):
        h = TimeSeriesHistory(run_id=run_id, action=action)
        db.add(h)
        db.commit()

timeseries_repository = TimeSeriesRepository()
