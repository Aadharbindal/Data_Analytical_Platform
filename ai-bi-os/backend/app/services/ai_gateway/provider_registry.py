from typing import List, Optional, Dict
from app.models.ai_gateway import CircuitState, ProviderStatus

_PRE_SEEDED_PROVIDERS = [
    {"name": "openai", "display_name": "OpenAI"},
    {"name": "anthropic", "display_name": "Anthropic"},
    {"name": "google", "display_name": "Google Gemini"},
    {"name": "deepseek", "display_name": "DeepSeek"},
    {"name": "mistral", "display_name": "Mistral"},
    {"name": "groq", "display_name": "Groq"},
    {"name": "ollama", "display_name": "Ollama"},
]

class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, dict] = {}
        self.initialize()
        
    def initialize(self):
        for p in _PRE_SEEDED_PROVIDERS:
            self._providers[p["name"]] = {
                **p,
                "status": ProviderStatus.ACTIVE,
                "circuit_state": CircuitState.CLOSED,
                "circuit_failure_count": 0,
                "priority": 100
            }
            
    def get_provider(self, name: str) -> Optional[dict]:
        return self._providers.get(name)
        
    def get_all_providers(self) -> List[dict]:
        return list(self._providers.values())
        
    def update_circuit_state(self, name: str, state: CircuitState, failure_count: int = 0):
        if name in self._providers:
            self._providers[name]["circuit_state"] = state
            self._providers[name]["circuit_failure_count"] = failure_count

provider_registry = ProviderRegistry()
