from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.schemas.vector import (
    EmbeddingGenerateRequest,
    EmbeddingGenerateResponse,
    VectorSearchRequest,
    VectorSearchResponse,
    ReindexRequest,
    ReindexResponse,
    StatisticsResponse,
    EmbeddingModelResponse
)
from app.services.vector.embedding_pipeline import EmbeddingPipeline
from app.services.vector.vector_search import VectorSearchService
from app.repositories.vector_repository import VectorRepository
from app.models.vector import EmbeddingObject, EmbeddingModel

router = APIRouter(prefix="/embeddings", tags=["vector-store"])

@router.post("/generate", response_model=EmbeddingGenerateResponse)
def generate_embeddings(request: EmbeddingGenerateRequest, db: Session = Depends(get_db)):
    pipeline = EmbeddingPipeline(db)
    try:
        saved_objects, metrics = pipeline.generate_and_store(request)
        return EmbeddingGenerateResponse(
            status="SUCCESS",
            embeddings=saved_objects,
            metrics=metrics
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bulk-generate", response_model=EmbeddingGenerateResponse)
def bulk_generate_embeddings(requests: List[EmbeddingGenerateRequest], background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # For a real implementation, this would process asynchronously in chunks.
    # We will run them synchronously for demonstration, but acknowledge the bulk nature.
    pipeline = EmbeddingPipeline(db)
    all_objects = []
    total_metrics = {"latency_ms": 0, "vector_count": 0}
    
    try:
        for request in requests:
            objs, metrics = pipeline.generate_and_store(request)
            all_objects.extend(objs)
            total_metrics["latency_ms"] += metrics.get("latency_ms", 0)
            total_metrics["vector_count"] += metrics.get("vector_count", 0)
            
        return EmbeddingGenerateResponse(
            status="BULK_SUCCESS",
            embeddings=all_objects,
            metrics=total_metrics
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{embedding_id}", response_model=Dict[str, Any])
def get_embedding(embedding_id: str, db: Session = Depends(get_db)):
    repo = VectorRepository(db)
    embedding = repo.get_embedding(embedding_id)
    if not embedding:
        raise HTTPException(status_code=404, detail="Embedding not found")
    
    return {
        "id": embedding.id,
        "workspace_id": embedding.workspace_id,
        "document_id": embedding.document_id,
        "dimensions": embedding.dimensions,
        "created_at": embedding.created_at
    }

@router.post("/search", response_model=VectorSearchResponse)
def search_vectors(request: VectorSearchRequest, db: Session = Depends(get_db)):
    search_service = VectorSearchService(db)
    try:
        results, metrics = search_service.search(request)
        return VectorSearchResponse(
            query=request.query_text,
            results=results,
            latency_ms=metrics.get("latency_ms", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reindex", response_model=ReindexResponse)
def reindex_vectors(request: ReindexRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # In a real app, this schedules a celery task
    return ReindexResponse(
        status="ACCEPTED",
        message=f"Reindexing started for index {request.index_name} with provider {request.provider}"
    )

@router.get("/models", response_model=List[EmbeddingModelResponse])
def get_embedding_models(db: Session = Depends(get_db)):
    repo = VectorRepository(db)
    models = repo.get_all_models()
    return models

@router.get("/statistics/summary", response_model=StatisticsResponse)
def get_statistics(db: Session = Depends(get_db)):
    repo = VectorRepository(db)
    stats = repo.get_statistics()
    return StatisticsResponse(**stats)
