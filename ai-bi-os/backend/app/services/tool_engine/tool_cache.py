import redis

class ToolCache:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 6):
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis_client.ping()
        except redis.ConnectionError:
            self.redis_client = None

    def invalidate(self, tool_id_string: str):
        if not self.redis_client:
            return
        keys = self.redis_client.keys(f"tool_engine:tool:{tool_id_string}:*")
        if keys:
            self.redis_client.delete(*keys)

tool_cache = ToolCache()
