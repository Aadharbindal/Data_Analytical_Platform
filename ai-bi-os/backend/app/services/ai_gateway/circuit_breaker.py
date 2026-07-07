import time
import logging
from app.models.ai_gateway import CircuitState
from app.services.ai_gateway.provider_registry import provider_registry

logger = logging.getLogger("CircuitBreaker")

class CircuitBreaker:
    """
    State machine for per-provider circuit breaking.
    CLOSED (normal) → 5 failures in 60s → OPEN (reject fast)
    OPEN → 30s cooldown → HALF-OPEN (test 1 request)
    HALF-OPEN success → CLOSED
    HALF-OPEN failure → OPEN
    """
    FAILURE_THRESHOLD = 5
    COOLDOWN_SECONDS = 30
    
    def __init__(self):
        # We track failures and timestamps in-memory for fast access
        self._state = {} # provider_name -> dict

    def _ensure_provider(self, provider_name: str):
        if provider_name not in self._state:
            self._state[provider_name] = {
                "failures": 0,
                "first_failure_time": 0,
                "last_failure_time": 0,
                "opened_time": 0
            }

    def check_request_allowed(self, provider_name: str) -> bool:
        provider = provider_registry.get_provider(provider_name)
        if not provider:
            return False
            
        state = provider["circuit_state"]
        
        if state == CircuitState.CLOSED:
            return True
            
        self._ensure_provider(provider_name)
            
        if state == CircuitState.OPEN:
            opened_time = self._state[provider_name]["opened_time"]
            if time.time() - opened_time >= self.COOLDOWN_SECONDS:
                # Cooldown passed, transition to half-open
                provider_registry.update_circuit_state(provider_name, CircuitState.HALF_OPEN)
                logger.warning(f"Circuit Breaker for {provider_name} entering HALF-OPEN state.")
                return True # Allow ONE request
            return False # Still open
            
        if state == CircuitState.HALF_OPEN:
            # Another request is already testing the circuit
            return False
            
        return True

    def record_success(self, provider_name: str):
        self._ensure_provider(provider_name)
        provider = provider_registry.get_provider(provider_name)
        if not provider: return
        
        if provider["circuit_state"] == CircuitState.HALF_OPEN:
            logger.info(f"Circuit Breaker for {provider_name} test succeeded, CLOSING circuit.")
            provider_registry.update_circuit_state(provider_name, CircuitState.CLOSED)
            
        # Reset counters
        self._state[provider_name]["failures"] = 0
        self._state[provider_name]["first_failure_time"] = 0

    def record_failure(self, provider_name: str):
        self._ensure_provider(provider_name)
        provider = provider_registry.get_provider(provider_name)
        if not provider: return
        
        now = time.time()
        p_state = self._state[provider_name]
        
        if provider["circuit_state"] == CircuitState.HALF_OPEN:
            # Failed the test, re-open immediately
            logger.error(f"Circuit Breaker for {provider_name} test failed, RE-OPENING circuit.")
            provider_registry.update_circuit_state(provider_name, CircuitState.OPEN)
            p_state["opened_time"] = now
            return
            
        if provider["circuit_state"] == CircuitState.CLOSED:
            # First failure in a new window?
            if p_state["failures"] == 0 or now - p_state["first_failure_time"] > 60:
                p_state["failures"] = 1
                p_state["first_failure_time"] = now
            else:
                p_state["failures"] += 1
                
            if p_state["failures"] >= self.FAILURE_THRESHOLD:
                logger.error(f"Circuit Breaker for {provider_name} TRIPPED (OPEN state).")
                provider_registry.update_circuit_state(provider_name, CircuitState.OPEN, p_state["failures"])
                p_state["opened_time"] = now

circuit_breaker = CircuitBreaker()
