from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.schemas.memory import (
    MemoryCreateRequest,
    MemoryUpdateRequest,
    MemorySearchRequest,
    MemoryResponse,
    MemoryHistoryResponse,
    MemoryStatisticsResponse
)
from app.services.memory.memory_manager import MemoryManager
from app.repositories.memory_repository import MemoryRepository

router = APIRouter(prefix="/memory", tags=["memory-engine"])

@router.post("/create", response_model=MemoryResponse)
def create_memory(request: MemoryCreateRequest, db: Session = Depends(get_db)):
    manager = MemoryManager(db)
    try:
        memory = manager.writer.write(request)
        return memory
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{memory_id}", response_model=MemoryResponse)
def get_memory(memory_id: str, db: Session = Depends(get_db)):
    manager = MemoryManager(db)
    memory = manager.retriever.get(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory

@router.post("/update", response_model=MemoryResponse)
def update_memory(memory_id: str, request: MemoryUpdateRequest, db: Session = Depends(get_db)):
    # Assuming full update logic would be in writer, stubbing here
    manager = MemoryManager(db)
    memory = manager.retriever.get(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    if request.summary:
        memory.summary = request.summary
    if request.importance_score is not None:
        memory.importance_score = request.importance_score
    if request.tags is not None:
        memory.tags = request.tags
        
    manager.repository.update_memory(memory)
    return memory

@router.post("/search", response_model=List[MemoryResponse])
def search_memories(request: MemorySearchRequest, db: Session = Depends(get_db)):
    manager = MemoryManager(db)
    try:
        results = manager.retriever.search(request)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/archive")
def archive_memory(memory_id: str, db: Session = Depends(get_db)):
    manager = MemoryManager(db)
    manager.writer.archive(memory_id)
    return {"status": "SUCCESS", "message": "Memory archived"}

@router.post("/restore")
def restore_memory(memory_id: str, db: Session = Depends(get_db)):
    manager = MemoryManager(db)
    manager.writer.restore(memory_id)
    return {"status": "SUCCESS", "message": "Memory restored"}

@router.delete("/{memory_id}")
def delete_memory(memory_id: str, db: Session = Depends(get_db)):
    repo = MemoryRepository(db)
    repo.delete_memory(memory_id)
    return {"status": "SUCCESS", "message": "Memory deleted"}

@router.get("/history/{memory_id}", response_model=List[MemoryHistoryResponse])
def get_memory_history(memory_id: str, db: Session = Depends(get_db)):
    repo = MemoryRepository(db)
    history = repo.get_history(memory_id)
    return history

@router.get("/statistics/summary", response_model=MemoryStatisticsResponse)
def get_statistics(db: Session = Depends(get_db)):
    repo = MemoryRepository(db)
    stats = repo.get_statistics()
    return MemoryStatisticsResponse(**stats)
