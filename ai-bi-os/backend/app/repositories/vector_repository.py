from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from app.models.vector import EmbeddingModel, EmbeddingObject, VectorIndex, EmbeddingMetrics

class VectorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_embedding_model(self, model_id: str) -> Optional[EmbeddingModel]:
        return self.db.query(EmbeddingModel).filter(EmbeddingModel.id == model_id).first()
        
    def get_embedding_model_by_name(self, name: str) -> Optional[EmbeddingModel]:
        return self.db.query(EmbeddingModel).filter(EmbeddingModel.name == name).first()

    def get_all_models(self) -> List[EmbeddingModel]:
        return self.db.query(EmbeddingModel).all()

    def create_embedding_model(self, model: EmbeddingModel) -> EmbeddingModel:
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def save_embeddings(self, embeddings: List[EmbeddingObject]) -> List[EmbeddingObject]:
        self.db.add_all(embeddings)
        self.db.commit()
        for e in embeddings:
            self.db.refresh(e)
        return embeddings
        
    def get_embedding(self, embedding_id: str) -> Optional[EmbeddingObject]:
        return self.db.query(EmbeddingObject).filter(EmbeddingObject.id == embedding_id).first()

    def get_vector_index(self, index_name: str) -> Optional[VectorIndex]:
        return self.db.query(VectorIndex).filter(VectorIndex.name == index_name).first()

    def log_metrics(self, metrics: EmbeddingMetrics):
        self.db.add(metrics)
        self.db.commit()

    def get_statistics(self) -> Dict[str, Any]:
        total_vectors = self.db.query(func.count(EmbeddingObject.id)).scalar() or 0
        total_models = self.db.query(func.count(EmbeddingModel.id)).scalar() or 0
        active_indices = self.db.query(func.count(VectorIndex.id)).filter(VectorIndex.status == "READY").scalar() or 0
        
        avg_latency = self.db.query(func.avg(EmbeddingMetrics.latency_ms)).filter(EmbeddingMetrics.operation == "GENERATION").scalar() or 0.0
        
        return {
            "total_vectors": total_vectors,
            "total_models": total_models,
            "active_indices": active_indices,
            "avg_latency_ms": float(avg_latency)
        }
