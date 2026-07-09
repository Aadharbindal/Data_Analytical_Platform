from fastapi import APIRouter
from pydantic import BaseModel
from app.services.data_processing import get_active_dataset, get_dataset_path
from app.services.query.duckdb_engine import DuckDBEngine
from app.ai.agents import AgentOrchestrator
import os

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/")
async def chat(request: ChatRequest):
    dataset_info = get_active_dataset()
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
        
        # Invoke AgentOrchestrator
        orchestrator = AgentOrchestrator()
        result = orchestrator.run_query(request.message, db_engine=engine)
        
        return {
            "response": result.get("final_insight"),
            "sql": result.get("executed_sql", [])
        }
    except Exception as e:
        return {"response": f"Error executing query: {str(e)}", "sql": []}
