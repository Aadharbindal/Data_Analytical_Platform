import hashlib
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.models.query import QueryCache

class QueryCacheManager:
    """Manages SQL hashing and retrieving cached result sets."""
    
    @staticmethod
    def _hash_query(sql: str, dataset_version_id: str) -> str:
        # Include version ID so cache automatically invalidates if dataset changes
        normalized = sql.lower().strip()
        payload = f"{normalized}_{dataset_version_id}".encode('utf-8')
        return hashlib.sha256(payload).hexdigest()
        
    @staticmethod
    def get_cached_result(db: Session, sql: str, dataset_version_id: str) -> Optional[Dict[str, Any]]:
        q_hash = QueryCacheManager._hash_query(sql, dataset_version_id)
        
        cache_entry = db.query(QueryCache).filter(
            QueryCache.query_hash == q_hash,
            QueryCache.expires_at > datetime.utcnow()
        ).first()
        
        if cache_entry:
            return cache_entry.result_data
        return None
        
    @staticmethod
    def set_cached_result(db: Session, sql: str, dataset_version_id: str, result_data: Dict[str, Any], ttl_minutes: int = 60):
        q_hash = QueryCacheManager._hash_query(sql, dataset_version_id)
        
        # Upsert
        cache_entry = db.query(QueryCache).filter(QueryCache.query_hash == q_hash).first()
        if not cache_entry:
            cache_entry = QueryCache(query_hash=q_hash)
            db.add(cache_entry)
            
        cache_entry.dataset_version_id = dataset_version_id
        cache_entry.result_data = result_data
        cache_entry.expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        cache_entry.created_at = datetime.utcnow()
        
        db.commit()
