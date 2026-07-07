from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any

from app.models.catalog import CatalogSearchIndex
from app.models.dataset import Dataset

class SearchEngine:
    """Executes ranked searches against the normalized search index."""
    
    @staticmethod
    def search(db: Session, query_string: str, limit: int = 20) -> List[Dict[str, Any]]:
        # Tokenize user query
        tokens = query_string.lower().replace("_", " ").split()
        if not tokens:
            return []
            
        # SQL-based ranked search:
        # Group by dataset_id, sum the weights where token is LIKE the query tokens.
        
        # Base query
        q = db.query(
            CatalogSearchIndex.dataset_id,
            func.sum(CatalogSearchIndex.weight).label('total_score')
        )
        
        # Add conditions for each token (Basic fuzzy/prefix match)
        conditions = []
        for token in tokens:
            conditions.append(CatalogSearchIndex.token.like(f"{token}%"))
            
        from sqlalchemy import or_
        q = q.filter(or_(*conditions))
        
        # Group and order
        q = q.group_by(CatalogSearchIndex.dataset_id).order_by(desc('total_score')).limit(limit)
        
        results = q.all()
        
        # Hydrate with dataset info
        final_results = []
        for row in results:
            ds_id = row.dataset_id
            score = row.total_score
            ds = db.query(Dataset).filter(Dataset.id == ds_id).first()
            if ds:
                final_results.append({
                    "dataset_id": ds.id,
                    "dataset_name": ds.name,
                    "relevance_score": score
                })
                
        return final_results
