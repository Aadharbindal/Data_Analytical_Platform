from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.data_processing import get_active_dataset, get_dataset_path
from app.services.query.duckdb_engine import DuckDBEngine
from app.ai.agents import AgentOrchestrator
from app.ai.governance import AIEvaluationFramework
from app.core.security import get_current_user
import os

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatFeedbackRequest(BaseModel):
    trace_id: str
    score: int
    comments: str = None

@router.post("")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        return {"response": "AI features are not configured - add GROQ_API_KEY to your .env file.", "sql": []}

    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"response": "No dataset uploaded yet.", "sql": None}
        
    filename_db = dataset_info.get("filepath")
    if not filename_db:
        return {"response": "Failed to load data.", "sql": None}
    filepath = get_dataset_path(filename_db)
    if not os.path.exists(filepath):
        return {"response": "Failed to load data.", "sql": None}

    # Determine format
    fmt = "csv"
    if filepath.endswith(".parquet"):
        fmt = "parquet"
    elif filepath.endswith(".json"):
        fmt = "json"
    elif filepath.endswith(".xlsx"):
        # Not natively supported by duckdb read_*, fallback to csv if possible or throw
        pass # duckdb will likely fail if we pass xlsx without spatial extension. For now, try csv format.

    try:
        # Initialize DuckDB Engine and register dataset
        engine = DuckDBEngine()
        
        # If it's xlsx, maybe we can register the df instead? DuckDB natively supports registering df.
        # But DuckDBEngine doesn't expose it. Let's just try register_dataset which is exposed.
        engine.register_dataset("active_dataset", filepath, format=fmt)
        
        # Invoke AgentOrchestrator        # We need the real user ID for RAG filtering
        user_id = current_user["id"]
        
        # We should instantiate the agent for each request right now or pass down context
        orchestrator = AgentOrchestrator()
        result = orchestrator.run_query(request.message, user_id=user_id, db_engine=engine)
        
        return {
            "response": result.get("final_insight"),
            "sql": result.get("executed_sql", []),
            "trace_id": result.get("trace_id")
        }
    except Exception as e:
        return {"response": f"Error executing query: {str(e)}", "sql": []}

@router.post("/feedback")
async def submit_chat_feedback(request: ChatFeedbackRequest, current_user: dict = Depends(get_current_user)):
    """Records human feedback (thumbs up/down, a 1-5 score, etc.) against a
    previously logged AI response, identified by the trace_id returned from
    POST /api/v1/chat."""
    if not (1 <= request.score <= 5):
        raise HTTPException(status_code=400, detail="score must be between 1 and 5")

    updated = AIEvaluationFramework().submit_human_feedback(request.trace_id, request.score, request.comments)
    if not updated:
        raise HTTPException(status_code=404, detail="No logged AI response found for that trace_id")

    return {"status": "ok"}
