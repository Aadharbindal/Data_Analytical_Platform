import logging
import hashlib
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.business_metrics import MetricCache

logger = logging.getLogger("MetricCache")

class MetricCacheManager:
    """
    Intelligent caching for business metrics.
    Generates deterministic cache keys based on metric logic and data slices.
    """
    
    def generate_cache_key(self, metric_id: str, dataset_version_id: str, 
                           dimension: str = None, dimension_value: str = None, 
                           time_window: str = None) -> str:
        
        components = f"{metric_id}|{dataset_version_id}|{dimension}|{dimension_value}|{time_window}"
        return hashlib.sha256(components.encode('utf-8')).hexdigest()

    def get_cached_result(self, db: Session, cache_key: str) -> Optional[float]:
        cache_entry = db.query(MetricCache).filter(
            MetricCache.cache_key == cache_key,
            MetricCache.is_valid == True,
            MetricCache.expires_at > datetime.utcnow()
        ).first()
        
        if cache_entry:
            return cache_entry.result_value
        return None
        
    def set_cached_result(self, db: Session, metric_id: str, dataset_version_id: str, 
                          cache_key: str, value: float, expires_in_seconds: int = 3600):
        
        import datetime as dt
        expires_at = datetime.utcnow() + dt.timedelta(seconds=expires_in_seconds)
        
        # Invalidate old cache if exists
        old_cache = db.query(MetricCache).filter(MetricCache.cache_key == cache_key).first()
        if old_cache:
            db.delete(old_cache)
            
        new_cache = MetricCache(
            cache_key=cache_key,
            metric_id=metric_id,
            dataset_version_id=dataset_version_id,
            result_value=value,
            expires_at=expires_at,
            is_valid=True
        )
        db.add(new_cache)
        db.commit()
        
    def invalidate_by_dataset(self, db: Session, dataset_version_id: str):
        """Invalidates all cached metrics for a specific dataset version."""
        db.query(MetricCache).filter(MetricCache.dataset_version_id == dataset_version_id).update({"is_valid": False})
        db.commit()

metric_cache_manager = MetricCacheManager()
