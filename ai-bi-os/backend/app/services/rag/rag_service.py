from app.schemas.rag import DocumentIndexRequest, DocumentResponse, RetrievalRequest, RetrievalResponse
from app.repositories.rag import KnowledgeRepository
from app.services.rag.chunk_manager import ChunkManager
from app.services.rag.knowledge_retrieval_engine import KnowledgeRetrievalEngine

class RAGService:
    """Bridging the API and specific engines."""
    
    def __init__(self, repository: KnowledgeRepository):
        self.repo = repository
        self.chunk_manager = ChunkManager()
        self.retrieval_engine = KnowledgeRetrievalEngine(repository)
        
    def index_document(self, request: DocumentIndexRequest) -> DocumentResponse:
        # 1. Create document record
        doc = self.repo.create_document(
            workspace_id=request.workspace_id,
            filename=request.filename,
            file_type=request.file_type,
            dataset_id=request.dataset_id
        )
        
        # 2. Chunk text
        chunks = self.chunk_manager.chunk_text(request.content)
        
        # 3. Save chunks
        for i, chunk_text in enumerate(chunks):
            self.repo.create_chunk(doc.id, i, chunk_text)
            
        # 4. Update status
        self.repo.update_document_status(doc.id, "INDEXED")
        
        # Return response
        return DocumentResponse(
            id=doc.id,
            workspace_id=doc.workspace_id,
            dataset_id=doc.dataset_id,
            filename=doc.filename,
            file_type=doc.file_type,
            status="INDEXED",
            created_at=doc.created_at
        )

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        return self.retrieval_engine.retrieve_and_rank(request)
