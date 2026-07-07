import time
from typing import List, Dict, Any, Tuple
import numpy as np

from app.models.vector import EmbeddingObject, EmbeddingMetrics
from app.schemas.vector import VectorSearchRequest
from app.repositories.vector_repository import VectorRepository
from app.services.vector.embedding_provider import EmbeddingProviderFactory

class SimilarityEngine:
    """Computes mathematical similarities if we are doing in-memory fallback."""
    
    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        dot_product = np.dot(v1, v2)
        norm_a = np.linalg.norm(v1)
        norm_b = np.linalg.norm(v2)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

class VectorSearchService:
    def __init__(self, db_session):
        self.db = db_session
        self.repository = VectorRepository(db_session)
        
    def search(self, request: VectorSearchRequest) -> Tuple[List[EmbeddingObject], Dict[str, Any]]:
        start_time = time.time()
        
        # 1. Embed the query text
        model_name = request.model_name or "text-embedding-3-small"
        provider_name = "openai" if "embedding-3" in model_name else "local"
        provider = EmbeddingProviderFactory.get_provider(provider_name)
        
        query_vectors = provider.generate_embeddings([request.query_text], model_name=model_name)
        query_vector = query_vectors[0]
        
        # 2. Retrieve vectors from DB (Fallback logic if no true Vector Store attached yet)
        # In a real setup, we would call VectorStoreFactory.get_provider("pgvector").search_vectors(...)
        # Here we mock retrieving everything in the workspace and doing in-memory similarity.
        # DO NOT DO THIS IN PRODUCTION FOR >10k VECTORS.
        
        all_embeddings = self.db.query(EmbeddingObject).filter(
            EmbeddingObject.workspace_id == request.workspace_id
        ).all()
        
        results = []
        for emb in all_embeddings:
            if not emb.vector_data:
                continue
                
            sim_score = SimilarityEngine.cosine_similarity(query_vector, emb.vector_data)
            
            if sim_score >= request.threshold:
                # Create a non-persistent copy for the result to include score
                result_obj = EmbeddingObject(
                    id=emb.id,
                    workspace_id=emb.workspace_id,
                    dataset_id=emb.dataset_id,
                    document_id=emb.document_id,
                    chunk_id=emb.chunk_id,
                    dimensions=emb.dimensions,
                    vector_data=emb.vector_data,
                    similarity_score=sim_score,
                    created_at=emb.created_at
                )
                results.append(result_obj)
                
        # 3. Sort by top_k
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        top_results = results[:request.top_k]
        
        # 4. Record Metrics
        latency_ms = int((time.time() - start_time) * 1000)
        metrics = EmbeddingMetrics(
            model_id=model_name,
            operation="SEARCH",
            latency_ms=latency_ms,
            vector_count=len(top_results)
        )
        self.repository.log_metrics(metrics)
        
        metrics_dict = {
            "latency_ms": latency_ms,
            "vector_count": len(top_results)
        }
        
        return top_results, metrics_dict
