from typing import List
import time
import uuid

from app.schemas.rag import RetrievalRequest, RetrievalResponse, ChunkResponse
from app.repositories.rag import KnowledgeRepository

class KnowledgeRetrievalEngine:
    """Coordinates the Knowledge Planner, Retriever, and Chunk Ranking Engine."""
    
    def __init__(self, repository: KnowledgeRepository):
        self.repo = repository
        
    def retrieve_and_rank(self, request: RetrievalRequest) -> RetrievalResponse:
        start_time = time.time()
        
        # 1. Retriever (Keyword Search for MVP)
        chunks = self.repo.search_chunks_by_keyword(
            workspace_id=request.workspace_id,
            query=request.query,
            top_k=request.top_k * 2 # Retrieve more for ranking
        )
        
        # 2. Chunk Ranking Engine (Mock semantic ranking)
        # Assign mock similarity scores based on simple string matching presence
        ranked_chunks = []
        for chunk in chunks:
            # Mock similarity score based on exact match vs partial
            score = 0.5
            if request.query.lower() in chunk.text_content.lower():
                score = 0.9
            
            ranked_chunks.append({
                "chunk": chunk,
                "score": score
            })
            
        # Sort by score descending
        ranked_chunks.sort(key=lambda x: x["score"], reverse=True)
        
        # Limit to top_k
        final_chunks = ranked_chunks[:request.top_k]
        
        response_chunks = []
        for rc in final_chunks:
            chunk = rc["chunk"]
            response_chunks.append(
                ChunkResponse(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    sequence_number=chunk.sequence_number,
                    text_content=chunk.text_content,
                    similarity_score=rc["score"]
                )
            )
            
        exec_time = int((time.time() - start_time) * 1000)
        
        # 3. Log retrieval history
        self.repo.log_retrieval(
            workspace_id=request.workspace_id,
            query_text=request.query,
            retrieved_count=len(response_chunks),
            time_ms=exec_time,
            cache_hit=False
        )
        
        return RetrievalResponse(
            retrieval_id=str(uuid.uuid4()),
            workspace_id=request.workspace_id,
            query=request.query,
            chunks=response_chunks,
            retrieval_time_ms=exec_time,
            cache_hit=False
        )
