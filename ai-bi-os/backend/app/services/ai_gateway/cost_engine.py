import logging
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.ai_gateway import ModelCost, ModelUsage, TaskType
from app.services.ai_gateway.model_registry import model_registry

logger = logging.getLogger("CostEngine")

class CostEngine:
    """
    Calculates costs based on tokens and writes to DB for tracking.
    """
    def calculate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        model = model_registry.get_model(model_id)
        if not model:
            logger.warning(f"CostEngine: Unknown model {model_id}, assuming zero cost.")
            return 0.0
            
        in_cost = (input_tokens / 1_000_000) * model["input_cost_per_1m"]
        out_cost = (output_tokens / 1_000_000) * model["output_cost_per_1m"]
        
        return in_cost + out_cost

    def record_usage(self, db: Session, request_id: str, model_id: str, 
                     input_tokens: int, output_tokens: int, 
                     workspace_id: str = None, user_id: str = None,
                     task_type: TaskType = None, latency_ms: float = None,
                     fallback_count: int = 0) -> float:
        
        cost = self.calculate_cost(model_id, input_tokens, output_tokens)
        
        # 1. Log individual usage
        usage = ModelUsage(
            request_id=request_id,
            model_id=model_id,
            workspace_id=workspace_id,
            user_id=user_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=cost,
            task_type=task_type,
            latency_ms=latency_ms,
            fallback_count=fallback_count
        )
        db.add(usage)
        
        # 2. Update Daily Aggregate
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        agg = db.query(ModelCost).filter(
            ModelCost.date == today_str,
            ModelCost.workspace_id == workspace_id,
            ModelCost.user_id == user_id,
            ModelCost.model_id_str == model_id
        ).first()
        
        if not agg:
            agg = ModelCost(
                date=today_str,
                workspace_id=workspace_id,
                user_id=user_id,
                model_id_str=model_id,
                provider_name=model_registry.get_model(model_id).get("provider_name") if model_registry.get_model(model_id) else None
            )
            db.add(agg)
            
        agg.total_requests += 1
        agg.total_input_tokens += input_tokens
        agg.total_output_tokens += output_tokens
        agg.total_cost_usd += cost
        
        db.commit()
        return cost

cost_engine = CostEngine()
