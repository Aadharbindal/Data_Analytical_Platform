from sqlalchemy.orm import Session
from app.models.kpi import KPICache, KPICalculation
from datetime import datetime, timedelta

class KPICacheManager:
    """Manages cached KPI calculation results."""
    
    @staticmethod
    def generate_cache_key(definition_id: str, dataset_version_id: str, dimension: str) -> str:
        dim_str = dimension or "GLOBAL"
        return f"kpi_{definition_id}_ds_{dataset_version_id}_dim_{dim_str}"
        
    @staticmethod
    def get_cached_result(db: Session, cache_key: str) -> bool:
        cache_entry = db.query(KPICache).filter(
            KPICache.cache_key == cache_key,
            KPICache.is_valid == True,
            KPICache.expires_at > datetime.utcnow()
        ).first()
        return cache_entry is not None
        
    @staticmethod
    def cache_result(db: Session, cache_key: str, calculation_id: str) -> None:
        # Invalidate old keys
        db.query(KPICache).filter(KPICache.cache_key == cache_key).update({"is_valid": False})
        
        new_cache = KPICache(
            cache_key=cache_key,
            calculation_id=calculation_id,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(new_cache)
