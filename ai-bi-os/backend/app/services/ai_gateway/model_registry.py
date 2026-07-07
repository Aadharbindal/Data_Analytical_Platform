from typing import List, Optional, Dict
from app.models.ai_gateway import AIModel

# Pre-seeded model registry as per requirements
_PRE_SEEDED_MODELS = [
    {
        "model_id": "gpt-4o",
        "provider_name": "openai",
        "display_name": "GPT-4o",
        "context_window": 128000,
        "supports_functions": True,
        "supports_vision": True,
        "input_cost_per_1m": 5.0,
        "output_cost_per_1m": 15.0,
    },
    {
        "model_id": "gpt-4o-mini",
        "provider_name": "openai",
        "display_name": "GPT-4o Mini",
        "context_window": 128000,
        "supports_functions": True,
        "supports_vision": True,
        "input_cost_per_1m": 0.15,
        "output_cost_per_1m": 0.60,
    },
    {
        "model_id": "gpt-3.5-turbo",
        "provider_name": "openai",
        "display_name": "GPT-3.5 Turbo",
        "context_window": 16384,
        "supports_functions": True,
        "supports_vision": False,
        "input_cost_per_1m": 0.50,
        "output_cost_per_1m": 1.50,
    },
    {
        "model_id": "claude-3-5-sonnet",
        "provider_name": "anthropic",
        "display_name": "Claude 3.5 Sonnet",
        "context_window": 200000,
        "supports_functions": True,
        "supports_vision": True,
        "input_cost_per_1m": 3.0,
        "output_cost_per_1m": 15.0,
    },
    {
        "model_id": "claude-3-haiku",
        "provider_name": "anthropic",
        "display_name": "Claude 3 Haiku",
        "context_window": 200000,
        "supports_functions": True,
        "supports_vision": True,
        "input_cost_per_1m": 0.25,
        "output_cost_per_1m": 1.25,
    },
    {
        "model_id": "gemini-1.5-pro",
        "provider_name": "google",
        "display_name": "Gemini 1.5 Pro",
        "context_window": 1000000,
        "supports_functions": True,
        "supports_vision": True,
        "input_cost_per_1m": 3.50,
        "output_cost_per_1m": 10.50,
    },
    {
        "model_id": "gemini-1.5-flash",
        "provider_name": "google",
        "display_name": "Gemini 1.5 Flash",
        "context_window": 1000000,
        "supports_functions": True,
        "supports_vision": True,
        "input_cost_per_1m": 0.075,
        "output_cost_per_1m": 0.30,
    },
    {
        "model_id": "deepseek-chat",
        "provider_name": "deepseek",
        "display_name": "DeepSeek Chat",
        "context_window": 128000,
        "supports_functions": True,
        "supports_vision": False,
        "input_cost_per_1m": 0.14,
        "output_cost_per_1m": 0.28,
    },
    {
        "model_id": "mixtral-8x7b",
        "provider_name": "mistral",
        "display_name": "Mixtral 8x7b",
        "context_window": 32768,
        "supports_functions": True,
        "supports_vision": False,
        "input_cost_per_1m": 0.70,
        "output_cost_per_1m": 0.70,
    },
    {
        "model_id": "llama-3-70b",
        "provider_name": "groq",
        "display_name": "Llama 3 70B",
        "context_window": 8192,
        "supports_functions": False,
        "supports_vision": False,
        "input_cost_per_1m": 0.59,
        "output_cost_per_1m": 0.79,
    },
]

class ModelRegistry:
    def __init__(self):
        # In memory store for speed, seeded at startup
        self._models: Dict[str, dict] = {}
        self.initialize()

    def initialize(self):
        for m in _PRE_SEEDED_MODELS:
            self._models[m["model_id"]] = m
            
    def get_model(self, model_id: str) -> Optional[dict]:
        return self._models.get(model_id)
        
    def get_all_models(self) -> List[dict]:
        return list(self._models.values())
        
    def get_models_by_provider(self, provider_name: str) -> List[dict]:
        return [m for m in self._models.values() if m["provider_name"] == provider_name]

model_registry = ModelRegistry()
