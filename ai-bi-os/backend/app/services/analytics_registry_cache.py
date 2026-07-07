import redis
import json
from typing import Optional, Any, Dict
from app.schemas.analytics_registry import AnalyticsObjectResponse
from pydantic import TypeAdapter

class AnalyticsRegistryCache:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis_client.ping()
        except redis.ConnectionError:
            self.redis_client = None

    def _get_key(self, object_id: str) -> str:
        return f"analytics_registry:obj:{object_id}"

    def get_object(self, object_id: str) -> Optional[AnalyticsObjectResponse]:
        if not self.redis_client:
            return None
        
        data = self.redis_client.get(self._get_key(object_id))
        if data:
            try:
                parsed = json.loads(data)
                return AnalyticsObjectResponse.model_validate(parsed)
            except Exception:
                return None
        return None

    def set_object(self, obj: AnalyticsObjectResponse, ttl_seconds: int = 3600):
        if not self.redis_client:
            return
        
        try:
            data = obj.model_dump_json()
            self.redis_client.setex(self._get_key(obj.id), ttl_seconds, data)
        except Exception:
            pass

    def invalidate_object(self, object_id: str):
        if not self.redis_client:
            return
        try:
            self.redis_client.delete(self._get_key(object_id))
        except Exception:
            pass

analytics_cache = AnalyticsRegistryCache()
