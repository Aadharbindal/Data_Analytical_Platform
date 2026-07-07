import time
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
import uuid

from app.models.vector import EmbeddingObject, EmbeddingMetrics
from app.schemas.vector import EmbeddingGenerateRequest
from app.repositories.vector_repository import VectorRepository
from app.services.vector.embedding_provider import EmbeddingProviderFactory

class EmbeddingPipeline:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.repository = VectorRepository(db_session)
        
    def _normalize_text(self, text: str) -> str:
        # Basic normalization: trim whitespace, etc.
        return " ".join(text.split())

    def _validate_texts(self, texts: List[str]) -> List[str]:
        valid_texts = []
        for t in texts:
            if t and len(t.strip()) > 0:
                valid_texts.append(t)
        return valid_texts

    def generate_and_store(self, request: EmbeddingGenerateRequest) -> Tuple[List[EmbeddingObject], Dict[str, Any]]:
        start_time = time.time()
        
        # 1. Text Normalization and Cleaning
        cleaned_texts = [self._normalize_text(t) for t in request.texts]
        
        # 2. Validation
        valid_texts = self._validate_texts(cleaned_texts)
        if not valid_texts:
            raise ValueError("No valid texts provided for embedding.")

        # 3. Retrieve Model Configuration
        model_name = request.model_name or "text-embedding-3-small"
        
        # This could fetch from repository, but we mock the mapping for now
        # Ideally: embedding_model = self.repository.get_embedding_model_by_name(model_name)
        # Using factory directly
        provider_name = "openai" if "embedding-3" in model_name else "local"
        provider = EmbeddingProviderFactory.get_provider(provider_name)
        
        dimensions = provider.get_dimensions(model_name)

        # 4. Generate Embeddings
        raw_vectors = provider.generate_embeddings(valid_texts, model_name=model_name)
        
        # 5. Attach Metadata and Create DB Objects
        embedding_objects = []
        for idx, vector in enumerate(raw_vectors):
            emb_obj = EmbeddingObject(
                workspace_id=request.workspace_id,
                dataset_id=request.dataset_id,
                document_id=request.document_id,
                chunk_id=str(uuid.uuid4()), # Assuming we assign chunk ID if not given, or usually passed in metadata
                vector_data=vector,
                dimensions=dimensions
            )
            embedding_objects.append(emb_obj)
            
        # 6. Store in Database
        saved_objects = self.repository.save_embeddings(embedding_objects)
        
        # 7. Record Metrics
        latency_ms = int((time.time() - start_time) * 1000)
        metrics = EmbeddingMetrics(
            model_id=model_name, # Storing name as ID for simplicity if model record doesn't exist
            operation="GENERATION",
            latency_ms=latency_ms,
            vector_count=len(saved_objects)
        )
        self.repository.log_metrics(metrics)
        
        metrics_dict = {
            "latency_ms": latency_ms,
            "vector_count": len(saved_objects),
            "model_name": model_name
        }
        
        return saved_objects, metrics_dict
