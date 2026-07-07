import logging
from typing import List, Callable, Any, Tuple
from app.services.ai_gateway.circuit_breaker import circuit_breaker

logger = logging.getLogger("FallbackManager")

# Hardcoded fallback chain per requirements
_FALLBACK_CHAIN = [
    "openai",
    "anthropic",
    "google",
    "deepseek",
    "mistral",
    "groq",
    "ollama"
]

class FallbackManager:
    """
    Executes the fallback chain if a provider fails or is tripped by circuit breaker.
    """
    
    def __init__(self):
        self.chain = _FALLBACK_CHAIN

    def _get_execution_chain(self, initial_provider: str) -> List[str]:
        """Returns the list of providers to try, starting with the initial_provider."""
        if initial_provider not in self.chain:
            return [initial_provider] + self.chain
            
        idx = self.chain.index(initial_provider)
        return self.chain[idx:]

    async def execute_with_fallback(self, initial_provider: str, operation: Callable[[str], Any]) -> Tuple[Any, str, List[str]]:
        """
        Executes the operation, advancing through the fallback chain on failure.
        operation must take the provider_name as its first argument.
        Returns (result, provider_used, fallback_chain_used)
        """
        providers_to_try = self._get_execution_chain(initial_provider)
        chain_used = []
        
        last_exception = None
        
        for provider_name in providers_to_try:
            if not circuit_breaker.check_request_allowed(provider_name):
                logger.info(f"Skipping {provider_name} due to open circuit.")
                continue
                
            try:
                chain_used.append(provider_name)
                result = await operation(provider_name)
                circuit_breaker.record_success(provider_name)
                return result, provider_name, chain_used
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed: {e}. Trying fallback.")
                circuit_breaker.record_failure(provider_name)
                last_exception = e
                
        raise Exception(f"All fallback providers failed. Last error: {last_exception}")

fallback_manager = FallbackManager()
