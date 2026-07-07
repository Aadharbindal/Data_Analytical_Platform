import pytest
from app.services.rag.chunk_manager import ChunkManager

def test_chunk_manager():
    manager = ChunkManager(chunk_size=10, chunk_overlap=2)
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = manager.chunk_text(text)
    
    # 0 to 10: "abcdefghij"
    # overlap 2 -> starts at 8
    # 8 to 18: "ijklmnopqr"
    # overlap 2 -> starts at 16
    # 16 to 26: "qrstuvwxyz"
    
    assert len(chunks) == 3
    assert chunks[0] == "abcdefghij"
    assert chunks[1] == "ijklmnopqr"
    assert chunks[2] == "qrstuvwxyz"

def test_chunk_manager_empty():
    manager = ChunkManager()
    chunks = manager.chunk_text("")
    assert len(chunks) == 0

def test_chunk_manager_small():
    manager = ChunkManager(chunk_size=100)
    chunks = manager.chunk_text("hello world")
    assert len(chunks) == 1
    assert chunks[0] == "hello world"
