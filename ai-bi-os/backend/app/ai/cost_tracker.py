import logging
from threading import Lock

logger = logging.getLogger("AI-BI-OS-CostTracker")

class CostTracker:
    """
    Tracks token usage and calculates estimated cost.
    In MVP, this is an in-memory Singleton. In production, this data would be written to PostgreSQL.
    """
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CostTracker, cls).__new__(cls)
                cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        # We assume standard GPT-4o pricing for MVP: 
        # $5.00 / 1M prompt tokens, $15.00 / 1M completion tokens
        self.pricing = {
            "prompt_per_1k": 0.005,
            "completion_per_1k": 0.015
        }
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_queries = 0

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculates the estimated cost in USD for a specific token count."""
        prompt_cost = (prompt_tokens / 1000) * self.pricing["prompt_per_1k"]
        completion_cost = (completion_tokens / 1000) * self.pricing["completion_per_1k"]
        return round(prompt_cost + completion_cost, 6)

    def record_usage(self, prompt_tokens: int, completion_tokens: int):
        """Records token usage for the global aggregate."""
        with self._lock:
            self.total_prompt_tokens += prompt_tokens
            self.total_completion_tokens += completion_tokens
            self.total_queries += 1
            logger.info(f"Recorded Usage: {prompt_tokens} prompt, {completion_tokens} completion")

    def get_aggregate_stats(self) -> dict:
        """Returns the global aggregate usage and cost."""
        with self._lock:
            total_cost = self.calculate_cost(self.total_prompt_tokens, self.total_completion_tokens)
            return {
                "total_queries": self.total_queries,
                "total_prompt_tokens": self.total_prompt_tokens,
                "total_completion_tokens": self.total_completion_tokens,
                "total_estimated_cost_usd": total_cost
            }
