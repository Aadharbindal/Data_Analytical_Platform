from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict

from app.core.database import get_db
from app.models.ai_gateway import TaskType
from app.schemas.ai_gateway import (
    GenerateRequest, GenerateResponse, ModelResponse, ProviderResponse,
    UsageStatsResponse, HealthResponse
)
from app.services.ai_gateway.ai_gateway import ai_gateway
from app.services.ai_gateway.model_registry import model_registry
from app.services.ai_gateway.provider_registry import provider_registry
from app.services.ai_gateway.model_router import model_router

router = APIRouter(prefix="/api/v1/ai", tags=["ai_gateway"])

@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest, db: Session = Depends(get_db)):
    """Synchronous generation using the AI Gateway."""
    try:
        response = await ai_gateway.generate(db, req)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def stream_generate(req: GenerateRequest, db: Session = Depends(get_db)):
    """Streaming generation using the AI Gateway."""
    # To implement SSE properly, we would return a StreamingResponse here
    # Since MVP is basic, we'll return a 501 for now to indicate SSE
    # needs Starlette StreamingResponse setup.
    raise HTTPException(status_code=501, detail="Streaming not yet fully wired to HTTP output in MVP")

@router.get("/models", response_model=List[ModelResponse])
async def get_models():
    """List all registered models."""
    models = model_registry.get_all_models()
    return [
        ModelResponse(
            id=m["model_id"],
            model_id=m["model_id"],
            display_name=m["display_name"],
            provider_name=m["provider_name"],
            context_window=m["context_window"],
            input_cost_per_1m=m["input_cost_per_1m"],
            output_cost_per_1m=m["output_cost_per_1m"],
            is_available=True,
            avg_latency_ms=None
        ) for m in models
    ]

@router.get("/providers", response_model=List[ProviderResponse])
async def get_providers():
    """List all providers."""
    providers = provider_registry.get_all_providers()
    return [
        ProviderResponse(
            id=p["name"],
            name=p["name"],
            display_name=p["display_name"],
            status=p["status"],
            circuit_state=p["circuit_state"]
        ) for p in providers
    ]

@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage(workspace_id: str = None, db: Session = Depends(get_db)):
    """Get usage stats (mocked for MVP)."""
    return UsageStatsResponse(
        workspace_id=workspace_id,
        total_requests=100,
        total_input_tokens=50000,
        total_output_tokens=10000,
        total_cost_usd=2.50
    )

@router.get("/costs")
async def get_costs(workspace_id: str = None, db: Session = Depends(get_db)):
    """Get cost breakdown."""
    return {"message": "Cost dashboard endpoint"}

@router.get("/health", response_model=List[HealthResponse])
async def get_health():
    """Provider health dashboard (mocked structure)."""
    from datetime import datetime
    providers = provider_registry.get_all_providers()
    return [
        HealthResponse(
            provider_name=p["name"],
            model_name=None,
            is_available=p["circuit_state"] != "open",
            p50_latency_ms=500,
            p95_latency_ms=1200,
            error_rate=0.0,
            last_checked_at=datetime.utcnow()
        ) for p in providers
    ]

@router.post("/router/test")
async def test_router(task_type: TaskType, max_cost_usd: float = None):
    """Test routing decision without executing."""
    try:
        model = model_router.route_request(
            task_type=task_type,
            max_cost_usd=max_cost_usd
        )
        return {"selected_model": model["model_id"], "provider": model["provider_name"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
