import logging
from typing import Optional, Dict, Any
import hashlib

logger = logging.getLogger("TrendCache")

class TrendCache:
    """In-memory cache for trend runs."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    def _get_key(self, dataset_version_id: str) -> str:
        return hashlib.md5(f"trend_{dataset_version_id}".encode()).hexdigest()

    def get_results(self, dataset_version_id: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(self._get_key(dataset_version_id))
        
    def set_results(self, dataset_version_id: str, results: Dict[str, Any]):
        self._cache[self._get_key(dataset_version_id)] = results
        
trend_cache = TrendCache()
