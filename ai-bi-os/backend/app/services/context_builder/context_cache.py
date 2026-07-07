import redis
import json
from typing import Optional
from app.schemas.context_builder import ContextObjectResponse

class ContextCache:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 1):
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis_client.ping()
        except redis.ConnectionError:
            self.redis_client = None

    def _get_key(self, context_id: str) -> str:
        return f"context_builder:obj:{context_id}"

    def get_context(self, context_id: str) -> Optional[ContextObjectResponse]:
        if not self.redis_client:
            return None
        
        data = self.redis_client.get(self._get_key(context_id))
        if data:
            try:
                parsed = json.loads(data)
                return ContextObjectResponse.model_validate(parsed)
            except Exception:
                return None
        return None

    def set_context(self, obj: ContextObjectResponse, ttl_seconds: int = 3600):
        if not self.redis_client:
            return
        
        try:
            data = obj.model_dump_json()
            self.redis_client.setex(self._get_key(obj.id), ttl_seconds, data)
        except Exception:
            pass

    def invalidate_context(self, context_id: str):
        if not self.redis_client:
            return
        try:
            self.redis_client.delete(self._get_key(context_id))
        except Exception:
            pass

context_cache = ContextCache()
