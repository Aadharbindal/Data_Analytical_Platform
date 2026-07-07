import redis
import json
from typing import Optional
from app.schemas.evidence import EvidenceObjectResponse

class EvidenceCache:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 2):
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis_client.ping()
        except redis.ConnectionError:
            self.redis_client = None

    def _get_key(self, evidence_id: str) -> str:
        return f"evidence_engine:obj:{evidence_id}"

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceObjectResponse]:
        if not self.redis_client:
            return None
        
        data = self.redis_client.get(self._get_key(evidence_id))
        if data:
            try:
                parsed = json.loads(data)
                return EvidenceObjectResponse.model_validate(parsed)
            except Exception:
                return None
        return None

    def set_evidence(self, obj: EvidenceObjectResponse, ttl_seconds: int = 3600):
        if not self.redis_client:
            return
        
        try:
            data = obj.model_dump_json()
            self.redis_client.setex(self._get_key(obj.id), ttl_seconds, data)
        except Exception:
            pass

    def invalidate_evidence(self, evidence_id: str):
        if not self.redis_client:
            return
        try:
            self.redis_client.delete(self._get_key(evidence_id))
        except Exception:
            pass

evidence_cache = EvidenceCache()
