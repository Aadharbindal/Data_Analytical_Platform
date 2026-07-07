import time
import uuid
import logging
import asyncio
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.ai_gateway import GatewayRequest, GatewayResponse, RequestStatus, TaskType
from app.schemas.ai_gateway import GenerateRequest, GenerateResponse, ProviderUsed
from app.services.ai_gateway.model_router import model_router
from app.services.ai_gateway.fallback_manager import fallback_manager
from app.services.ai_gateway.retry_manager import retry_manager
from app.services.ai_gateway.cost_engine import cost_engine
from app.services.ai_gateway.latency_engine import latency_engine
from app.services.ai_gateway.token_manager import token_manager

logger = logging.getLogger("AIGateway")

class AIGateway:
    """
    Main orchestrator for AI calls.
    Routes -> Retries -> Fallbacks -> Costs -> Audits.
    """
    
    async def _mock_provider_call(self, provider_name: str, model_id: str, prompt: str) -> dict:
        """Mock LLM call for the MVP"""
        await asyncio.sleep(0.5) # Simulate network latency
        
        # Simulate an error for testing circuit breakers if needed
        if provider_name == "deepseek" and "fail" in prompt.lower():
            raise Exception("Provider API Error")
            
        return {
            "content": f"Mock response from {model_id} via {provider_name}.",
            "finish_reason": "stop",
            "input_tokens": token_manager.estimate_tokens(prompt),
            "output_tokens": 50,
        }

    async def generate(self, db: Session, req: GenerateRequest) -> GenerateResponse:
        start_time = time.time()
        
        # 1. Audit Request Entry
        prompt = "\n".join(m.content for m in req.messages)
        db_req = GatewayRequest(
            workspace_id=req.workspace_id,
            user_id=req.user_id,
            task_type=req.task_type,
            status=RequestStatus.PROCESSING,
            messages_count=len(req.messages),
            # In prod, redact PII before saving prompt_preview
            prompt_preview=prompt[:200]
        )
        db.add(db_req)
        db.commit()
        db.refresh(db_req)
        
        # 2. Routing Decision
        target_model = model_router.route_request(
            task_type=req.task_type,
            max_cost_usd=req.max_cost_usd,
            max_latency_ms=req.max_latency_ms,
            preferred_model=req.preferred_model
        )
        
        initial_provider = target_model["provider_name"]
        db_req.resolved_model = target_model["model_id"]
        db_req.resolved_provider = initial_provider
        db.commit()

        # 3. Execution (with Retry & Fallback)
        async def provider_operation(provider_name: str):
            # In a real system, we'd lookup the specific model for the fallback provider.
            # For simplicity, if we fallback, we just use the default model of that provider.
            # Or pass the task_type to select the best model for the fallback provider.
            model_id = target_model["model_id"] if provider_name == initial_provider else f"{provider_name}-fallback-model"
            
            # The actual retry loop wraps the provider call
            return await retry_manager.execute_with_retry(
                self._mock_provider_call, provider_name, model_id, prompt
            )
            
        try:
            result, final_provider, chain_used = await fallback_manager.execute_with_fallback(
                initial_provider, provider_operation
            )
        except Exception as e:
            db_req.status = RequestStatus.FAILED
            db_req.completed_at = datetime.utcnow()
            db.commit()
            raise Exception(f"AI Gateway failed to execute request: {e}")

        # 4. Metrics & Costs
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        final_model_id = target_model["model_id"] if final_provider == initial_provider else f"{final_provider}-fallback-model"
        fallback_used = len(chain_used) > 1
        
        # We assume cost_engine handles models not in registry gracefully
        cost = cost_engine.record_usage(
            db=db,
            request_id=db_req.id,
            model_id=final_model_id,
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            workspace_id=req.workspace_id,
            user_id=req.user_id,
            task_type=req.task_type,
            latency_ms=latency_ms,
            fallback_count=len(chain_used) - 1
        )
        
        latency_engine.record_latency(db, final_provider, final_model_id, latency_ms, True)

        # 5. Audit Request Exit
        db_res = GatewayResponse(
            request_id=db_req.id,
            content=result["content"],
            finish_reason=result["finish_reason"],
            model_used=final_model_id,
            provider_used=final_provider,
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            cost_usd=cost,
            latency_ms=latency_ms,
            fallback_used=fallback_used,
            fallback_chain=chain_used, # Store as JSON list
            retry_count=0 # Simplified, actual retry manager could track this
        )
        db.add(db_res)
        
        db_req.status = RequestStatus.COMPLETED
        db_req.completed_at = datetime.utcnow()
        db_req.fallback_count = len(chain_used) - 1
        db.commit()

        # Build response
        fallback_details = [
            ProviderUsed(provider_name=p, model_name=f"{p}-model", latency_ms=0)
            for p in chain_used
        ]

        return GenerateResponse(
            content=result["content"],
            finish_reason=result["finish_reason"],
            model_used=final_model_id,
            provider_used=final_provider,
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            cost_usd=cost,
            latency_ms=latency_ms,
            fallback_used=fallback_used,
            fallback_chain=fallback_details,
            retry_count=0
        )

ai_gateway = AIGateway()
