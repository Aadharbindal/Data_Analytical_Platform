from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.rag import (
    DocumentIndexRequest,
    DocumentResponse,
    RetrievalRequest,
    RetrievalResponse,
    SearchRequest,
    ChunkResponse,
    HistoryResponse
)
from app.repositories.rag import KnowledgeRepository
from app.services.rag.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["RAG Engine"])

def get_rag_service(db: Session = Depends(get_db)) -> RAGService:
    repo = KnowledgeRepository(db)
    return RAGService(repo)

@router.post("/index", response_model=DocumentResponse)
def index_document(request: DocumentIndexRequest, service: RAGService = Depends(get_rag_service)):
    """Index a document by chunking it."""
    return service.index_document(request)

@router.post("/retrieve", response_model=RetrievalResponse)
def retrieve(request: RetrievalRequest, service: RAGService = Depends(get_rag_service)):
    """Retrieve relevant chunks for an AI Request."""
    return service.retrieve(request)

@router.post("/search", response_model=List[ChunkResponse])
def search(request: SearchRequest, service: RAGService = Depends(get_rag_service)):
    """Direct search endpoint for users."""
    retrieval_req = RetrievalRequest(
        workspace_id=request.workspace_id,
        query=request.query,
        top_k=request.top_k
    )
    result = service.retrieve(retrieval_req)
    return result.chunks

@router.get("/documents", response_model=List[DocumentResponse])
def get_documents(workspace_id: str, db: Session = Depends(get_db)):
    """Get indexed documents for a workspace."""
    repo = KnowledgeRepository(db)
    docs = repo.get_documents_by_workspace(workspace_id)
    return docs

@router.get("/chunks", response_model=List[ChunkResponse])
def get_chunks(workspace_id: str, db: Session = Depends(get_db)):
    """Get indexed chunks for a workspace."""
    repo = KnowledgeRepository(db)
    chunks = repo.get_chunks_by_workspace(workspace_id)
    return chunks

@router.get("/history", response_model=List[HistoryResponse])
def get_history(workspace_id: str, db: Session = Depends(get_db)):
    """Get retrieval history for a workspace."""
    repo = KnowledgeRepository(db)
    history = repo.get_history(workspace_id)
    return history

@router.post("/reindex")
def reindex_document(workspace_id: str):
    """Trigger a re-index for the workspace (placeholder)."""
    return {"status": "Re-indexing started for workspace " + workspace_id}
