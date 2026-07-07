import logging
from typing import Optional, Dict
from app.models.ai_gateway import TaskType
from app.services.ai_gateway.model_registry import model_registry
from app.services.ai_gateway.capability_registry import capability_registry
from app.services.ai_gateway.provider_registry import provider_registry
from app.services.ai_gateway.circuit_breaker import circuit_breaker

logger = logging.getLogger("ModelRouter")

class ModelRouter:
    """
    Decides the best model based on a multi-dimensional scoring algorithm.
    """
    def route_request(self, task_type: TaskType, max_cost_usd: float = None, 
                      max_latency_ms: float = None, preferred_model: str = None) -> Dict:
        """
        Returns the selected model dict.
        """
        # 1. Respect strict preference if it's available
        if preferred_model:
            model = model_registry.get_model(preferred_model)
            if model:
                provider_name = model["provider_name"]
                if circuit_breaker.check_request_allowed(provider_name):
                    return model
                    
        # 2. Get capability mapping for the task
        mappings = capability_registry.get_preferred_models_for_task(task_type)
        default_model_id = mappings["default"]
        fallback_model_id = mappings["fallback"]
        
        # 3. Check default model
        default_model = model_registry.get_model(default_model_id)
        if default_model:
            provider_name = default_model["provider_name"]
            if circuit_breaker.check_request_allowed(provider_name):
                # Optionally check max_cost here
                return default_model
                
        # 4. Check fallback model
        fallback_model = model_registry.get_model(fallback_model_id)
        if fallback_model:
            provider_name = fallback_model["provider_name"]
            if circuit_breaker.check_request_allowed(provider_name):
                return fallback_model
                
        # 5. Desperation: find any model from an allowed provider
        for model in model_registry.get_all_models():
            if circuit_breaker.check_request_allowed(model["provider_name"]):
                return model
                
        raise Exception("ModelRouter: No available models. All circuits might be open.")

model_router = ModelRouter()
