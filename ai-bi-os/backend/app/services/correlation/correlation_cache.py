import logging
from typing import Optional, Dict, Any
import hashlib

logger = logging.getLogger("CorrelationCache")

class CorrelationCache:
    """
    In-memory cache for MVP to store intermediate correlation results.
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    def _get_key(self, dataset_version_id: str) -> str:
        return hashlib.md5(f"corr_{dataset_version_id}".encode()).hexdigest()

    def get_results(self, dataset_version_id: str) -> Optional[Dict[str, Any]]:
        key = self._get_key(dataset_version_id)
        return self._cache.get(key)
        
    def set_results(self, dataset_version_id: str, results: Dict[str, Any]):
        key = self._get_key(dataset_version_id)
        self._cache[key] = results
        
    def invalidate_dataset(self, dataset_version_id: str):
        key = self._get_key(dataset_version_id)
        if key in self._cache:
            del self._cache[key]

correlation_cache = CorrelationCache()
