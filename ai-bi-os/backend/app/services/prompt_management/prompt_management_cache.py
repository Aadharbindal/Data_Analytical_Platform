import redis
import json
from typing import Optional

class PromptManagementCache:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 4):
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis_client.ping()
        except redis.ConnectionError:
            self.redis_client = None

    def invalidate_cache(self, template_id: str):
        if not self.redis_client:
            return
        keys = self.redis_client.keys(f"prompt_management:*:{template_id}:*")
        if keys:
            self.redis_client.delete(*keys)

pm_cache = PromptManagementCache()
