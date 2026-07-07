import redis
import json
from typing import Optional
from app.schemas.prompt import PromptObjectResponse

class PromptCache:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 3):
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis_client.ping()
        except redis.ConnectionError:
            self.redis_client = None

    def _get_key(self, prompt_id: str) -> str:
        return f"prompt_engine:obj:{prompt_id}"

    def get_prompt(self, prompt_id: str) -> Optional[PromptObjectResponse]:
        if not self.redis_client:
            return None
        
        data = self.redis_client.get(self._get_key(prompt_id))
        if data:
            try:
                parsed = json.loads(data)
                return PromptObjectResponse.model_validate(parsed)
            except Exception:
                return None
        return None

    def set_prompt(self, obj: PromptObjectResponse, ttl_seconds: int = 3600):
        if not self.redis_client:
            return
        
        try:
            data = obj.model_dump_json()
            self.redis_client.setex(self._get_key(obj.id), ttl_seconds, data)
        except Exception:
            pass

prompt_cache = PromptCache()
