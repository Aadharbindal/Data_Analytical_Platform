import logging
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.ai_gateway import ModelHealth

logger = logging.getLogger("LatencyEngine")

class LatencyEngine:
    """
    Records and tracks latencies for models and providers.
    """
    def record_latency(self, db: Session, provider_id: str, model_id: str, latency_ms: float, success: bool):
        # We find or create the current health record for today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        record = db.query(ModelHealth).filter(
            ModelHealth.provider_id == provider_id,
            ModelHealth.model_id == model_id,
            ModelHealth.last_checked_at >= today
        ).first()
        
        if not record:
            record = ModelHealth(
                provider_id=provider_id,
                model_id=model_id,
                last_checked_at=datetime.utcnow()
            )
            db.add(record)
            
        if success:
            record.success_count += 1
            # Simple EMA for latency
            if record.latency_ms is None:
                record.latency_ms = latency_ms
            else:
                record.latency_ms = (record.latency_ms * 0.9) + (latency_ms * 0.1)
        else:
            record.failure_count += 1
            
        total = record.success_count + record.failure_count
        if total > 0:
            record.error_rate = record.failure_count / total
            
        record.last_checked_at = datetime.utcnow()
        db.commit()

latency_engine = LatencyEngine()
