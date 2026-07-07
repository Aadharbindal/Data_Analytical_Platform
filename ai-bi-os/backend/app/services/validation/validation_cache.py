import logging
from typing import Optional, Dict, Any
import hashlib

logger = logging.getLogger("ValidationCache")

class ValidationCache:
    """In-memory cache for validation runs."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    def _get_key(self, target_id: str, target_type: str) -> str:
        return hashlib.md5(f"val_{target_type}_{target_id}".encode()).hexdigest()

    def get_results(self, target_id: str, target_type: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(self._get_key(target_id, target_type))
        
    def set_results(self, target_id: str, target_type: str, results: Dict[str, Any]):
        self._cache[self._get_key(target_id, target_type)] = results
        
validation_cache = ValidationCache()
