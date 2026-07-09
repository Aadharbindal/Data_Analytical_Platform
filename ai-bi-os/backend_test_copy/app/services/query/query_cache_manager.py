import hashlib
from typing import Dict, Any, Optional

# In-memory mock cache to bypass SQLAlchemy requirement
_mock_cache = {}

class QueryCacheManager:
    """Manages SQL hashing and retrieving cached result sets."""
    
    @staticmethod
    def _hash_query(sql: str, dataset_version_id: str) -> str:
        # Include version ID so cache automatically invalidates if dataset changes
        normalized = sql.lower().strip()
        payload = f"{normalized}_{dataset_version_id}".encode('utf-8')
        return hashlib.sha256(payload).hexdigest()
        
    @staticmethod
    def get_cached_result(db: Any, sql: str, dataset_version_id: str) -> Optional[Dict[str, Any]]:
        q_hash = QueryCacheManager._hash_query(sql, dataset_version_id)
        return _mock_cache.get(q_hash)
        
    @staticmethod
    def set_cached_result(db: Any, sql: str, dataset_version_id: str, result_data: Dict[str, Any], ttl_minutes: int = 60):
        q_hash = QueryCacheManager._hash_query(sql, dataset_version_id)
        _mock_cache[q_hash] = result_data
