import redis

class OrchestratorCache:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 5):
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis_client.ping()
        except redis.ConnectionError:
            self.redis_client = None

    def invalidate(self, execution_id: str):
        if not self.redis_client:
            return
        keys = self.redis_client.keys(f"orchestrator:execution:{execution_id}:*")
        if keys:
            self.redis_client.delete(*keys)

orc_cache = OrchestratorCache()
