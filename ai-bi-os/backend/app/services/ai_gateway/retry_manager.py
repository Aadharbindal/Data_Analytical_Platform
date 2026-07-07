import asyncio
import random
import logging
from typing import Callable, Any

logger = logging.getLogger("RetryManager")

class RetryManager:
    """
    Handles retries with exponential backoff and jitter.
    Used before falling back to another provider.
    """
    MAX_RETRIES = 3
    BASE_DELAY = 1.0 # seconds
    
    async def execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        attempts = 0
        while True:
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                attempts += 1
                if attempts > self.MAX_RETRIES:
                    logger.error(f"Operation failed after {self.MAX_RETRIES} retries. Last error: {e}")
                    raise
                    
                # Exponential backoff with jitter
                delay = self.BASE_DELAY * (2 ** (attempts - 1))
                jitter = random.uniform(0, 0.1 * delay)
                sleep_time = delay + jitter
                
                logger.warning(f"Operation failed: {e}. Retrying in {sleep_time:.2f}s (Attempt {attempts}/{self.MAX_RETRIES})")
                await asyncio.sleep(sleep_time)

retry_manager = RetryManager()
