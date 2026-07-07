import logging
import json
import os

logger = logging.getLogger("AI-BI-OS-EventBus")

class PluggableEventBus:
    """
    Abstracts the Event Bus.
    Can be backed by Memory (Dev), Redis Streams (MVP), or Kafka (Enterprise).
    """
    def __init__(self):
        self.backend = os.getenv("EVENT_BUS_BACKEND", "memory")
        if self.backend == "redis":
            import redis
            # In docker, the host will be 'redis'
            redis_host = os.getenv("REDIS_HOST", "localhost")
            self.redis_client = redis.Redis(host=redis_host, port=6379, db=0)
        else:
            self.memory_stream = []

    def publish(self, topic: str, event_data: dict):
        """Publishes an event to the stream."""
        payload = json.dumps(event_data)
        if self.backend == "redis":
            try:
                self.redis_client.xadd(topic, {"payload": payload})
                logger.info(f"[Redis Event] Published to {topic}")
            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}")
        else:
            self.memory_stream.append({"topic": topic, "data": payload})
            logger.info(f"[Memory Event] Published to {topic}: {payload}")
