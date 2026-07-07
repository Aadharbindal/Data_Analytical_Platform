import logging
from typing import Optional, Dict, Any
import hashlib

logger = logging.getLogger("EDACache")

class EDACache:
    """
    In-memory cache for MVP to store intermediate EDA stats during parallel profiling.
    Prevents redundant recalculations on the same dataset version.
    """
    
    def __init__(self):
        # Key: dataset_version_id, Value: Dict of stats
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    def _get_key(self, dataset_version_id: str, column_name: str) -> str:
        return hashlib.md5(f"{dataset_version_id}_{column_name}".encode()).hexdigest()

    def get_column_stats(self, dataset_version_id: str, column_name: str) -> Optional[Dict[str, Any]]:
        key = self._get_key(dataset_version_id, column_name)
        return self._cache.get(key)
        
    def set_column_stats(self, dataset_version_id: str, column_name: str, stats: Dict[str, Any]):
        key = self._get_key(dataset_version_id, column_name)
        self._cache[key] = stats
        
    def invalidate_dataset(self, dataset_version_id: str):
        # MVP simple clear
        keys_to_delete = [k for k in self._cache.keys() if dataset_version_id in k]
        for k in keys_to_delete:
            del self._cache[k]

eda_cache = EDACache()
