from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
import pandas as pd
import io

from app.services.connector import ConnectorFactory
from app.services.duckdb_engine import DuckDBEngine
from app.api import export
from app.api.analytics_registry_router import router as analytics_registry_router
from app.api.context_router import router as context_router
from app.api.evidence_router import router as evidence_router
from app.api.prompt_router import router as prompt_router
from app.api.prompt_management_router import router as prompt_management_router
from app.api.orchestrator_router import router as orchestrator_router
from app.api.tools_router import router as tools_router
from app.api.sql_agent_router import router as sql_agent_router
from app.api.python_agent_router import router as python_agent_router
from app.api.rag_router import router as rag_router
from app.api.vector import router as vector_router
from app.api.memory import router as memory_router
from app.api.conversation import router as conversation_router
from app.api.insight_generation_router import router as insight_generation_router
from app.api.recommendation_intelligence_router import router as recommendation_intelligence_router
from app.api.decision_intelligence_router import router as decision_intelligence_router
from app.api.business_rule_engine_router import router as business_rule_engine_router
from app.api.ai_validation_engine_router import router as ai_validation_engine_router
from app.api.ai_evaluation_engine_router import router as ai_evaluation_engine_router
from app.api.multi_agent_coordinator_router import router as multi_agent_coordinator_router
router = APIRouter()
router.include_router(export.router, prefix="/export", tags=["export"])
router.include_router(analytics_registry_router)
router.include_router(context_router)
router.include_router(evidence_router)
router.include_router(prompt_router)
router.include_router(prompt_management_router)
router.include_router(orchestrator_router)
router.include_router(tools_router)
router.include_router(sql_agent_router)
router.include_router(python_agent_router)
router.include_router(rag_router)
router.include_router(vector_router)
router.include_router(memory_router)
router.include_router(conversation_router)
router.include_router(insight_generation_router)
router.include_router(recommendation_intelligence_router)
router.include_router(decision_intelligence_router)
router.include_router(business_rule_engine_router)
router.include_router(ai_validation_engine_router)
router.include_router(ai_evaluation_engine_router)
router.include_router(multi_agent_coordinator_router)
db_engine = DuckDBEngine() # In-memory instance for the slice

@router.post("/api/v1/upload")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported for MVP.")
    
    content = await file.read()
    
    try:
        # 1. Connect & Parse
        connector = ConnectorFactory.get_connector("csv", file_content=content)
        df = connector.fetch_data()
        
        # 2. Register in DuckDB
        table_name = "current_dataset"
        db_engine.load_dataframe(table_name, df)
        
        return {"status": "success", "message": f"Successfully loaded {len(df)} rows."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/analytics/kpis")
async def get_kpis():
    try:
        # Execute DuckDB queries to get high level stats
        # We assume numeric columns exist. In a real scenario, we'd query information_schema.
        query = """
        SELECT 
            COUNT(*) as total_rows
        FROM current_dataset
        """
        res_df = db_engine.execute_query(query)
        if res_df.empty:
            return {"error": "No data found"}
            
        stats = res_df.to_dict(orient="records")[0]
        
        # Try to find a numeric column to sum/avg
        numeric_cols_query = "SELECT column_name FROM information_schema.columns WHERE table_name='current_dataset' AND data_type IN ('BIGINT', 'DOUBLE', 'INTEGER')"
        num_cols = db_engine.execute_query(numeric_cols_query)
        
        kpis = [{"title": "Total Records", "value": str(stats["total_rows"]), "trend": 0}]
        
        if not num_cols.empty:
            first_num = num_cols.iloc[0]['column_name']
            val_query = f"SELECT SUM({first_num}) as total_sum, AVG({first_num}) as avg_val FROM current_dataset"
            val_res = db_engine.execute_query(val_query)
            if not val_res.empty:
                kpis.append({"title": f"Total {first_num}", "value": f"{val_res.iloc[0]['total_sum']:.2f}"})
                kpis.append({"title": f"Average {first_num}", "value": f"{val_res.iloc[0]['avg_val']:.2f}"})

        # Try to generate generic chart data from numeric columns
        chart_data = []
        try:
            # Get the first numeric column
            num_cols_df = db_engine.execute_query("SELECT column_name FROM information_schema.columns WHERE table_name='current_dataset' AND data_type IN ('BIGINT', 'DOUBLE', 'INTEGER')")
            numeric_cols = num_cols_df['column_name'].tolist() if not num_cols_df.empty else []
            
            # Get the first string/categorical column for the X axis
            cat_cols_df = db_engine.execute_query("SELECT column_name FROM information_schema.columns WHERE table_name='current_dataset' AND data_type IN ('VARCHAR', 'STRING')")
            cat_cols = cat_cols_df['column_name'].tolist() if not cat_cols_df.empty else []
            
            if numeric_cols and cat_cols:
                # Group by the first categorical column, sum the first numeric column, get top 10
                sql = f"SELECT {cat_cols[0]} as name, SUM({numeric_cols[0]}) as value FROM current_dataset GROUP BY 1 ORDER BY 2 DESC LIMIT 10"
                chart_df = db_engine.execute_query(sql)
                # Convert to dict array
                chart_data = chart_df.to_dict(orient="records")
            else:
                # Fallback to random data for visual proof if no grouping is possible
                chart_data = [
                    {"name": "Jan", "value": 400},
                    {"name": "Feb", "value": 300},
                    {"name": "Mar", "value": 550},
                    {"name": "Apr", "value": 450}
                ]
        except Exception:
            chart_data = []

        return {
            "kpis": kpis,
            "chart_data": chart_data,
            "message": "Data processed successfully"
        }
    except Exception as e:
        return {"error": str(e)}

from pydantic import BaseModel
from app.ai.agents import AgentOrchestrator

class ChatRequest(BaseModel):
    message: str
    
orchestrator = AgentOrchestrator()

@router.post("/api/v1/chat")
async def chat_with_agent(req: ChatRequest):
    try:
        # Pass the current active DB engine so the LLM can query it
        result = orchestrator.run_query(req.message, db_engine=db_engine)
        return {
            "response": result["final_insight"],
            "executed_sql": result.get("executed_sql", []),
            "cost_estimate": result.get("cost_estimate", 0.0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/admin/costs")
async def get_admin_costs():
    """Returns global aggregate token usage and estimated cost."""
    from app.ai.cost_tracker import CostTracker
    tracker = CostTracker()
    return tracker.get_aggregate_stats()

@router.post("/api/v1/chat/async")
async def chat_with_agent_async(req: ChatRequest):
    """
    Enterprise Non-blocking Endpoint.
    Submits the query to Celery and returns a Task ID instantly.
    """
    try:
        from app.worker import process_ai_query
        task = process_ai_query.delay(req.message)
        return {"task_id": task.id, "status": "Processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/chat/status/{task_id}")
async def get_chat_status(task_id: str):
    """
    Endpoint for the frontend to poll the task status.
    """
    from app.worker import celery_app
    task = celery_app.AsyncResult(task_id)
    if task.state == 'PENDING':
        return {"status": "Pending"}
    elif task.state == 'SUCCESS':
        return {"status": "Complete", "result": task.result}
    else:
        return {"status": task.state}
