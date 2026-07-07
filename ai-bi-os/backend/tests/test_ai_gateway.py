import pytest
import asyncio
from unittest.mock import patch, MagicMock

from app.models.ai_gateway import TaskType, CircuitState
from app.services.ai_gateway.model_router import model_router
from app.services.ai_gateway.circuit_breaker import circuit_breaker
from app.services.ai_gateway.provider_registry import provider_registry
from app.services.ai_gateway.fallback_manager import fallback_manager

def test_model_router_default():
    """Test default routing for CHAT task"""
    model = model_router.route_request(task_type=TaskType.CHAT)
    assert model["model_id"] == "gpt-4o-mini"
    assert model["provider_name"] == "openai"

def test_model_router_preferred():
    """Test routing with strict preferred model"""
    model = model_router.route_request(
        task_type=TaskType.CHAT, 
        preferred_model="claude-3-5-sonnet"
    )
    assert model["model_id"] == "claude-3-5-sonnet"
    assert model["provider_name"] == "anthropic"

def test_circuit_breaker_state_transitions():
    """Test circuit breaker OPEN logic"""
    provider_name = "test_provider"
    
    # Register mock provider
    provider_registry._providers[provider_name] = {
        "name": provider_name,
        "circuit_state": CircuitState.CLOSED,
        "circuit_failure_count": 0
    }
    
    assert circuit_breaker.check_request_allowed(provider_name) is True
    
    # Trip circuit
    for _ in range(5):
        circuit_breaker.record_failure(provider_name)
        
    assert provider_registry._providers[provider_name]["circuit_state"] == CircuitState.OPEN
    assert circuit_breaker.check_request_allowed(provider_name) is False

@pytest.mark.asyncio
async def test_fallback_manager():
    """Test the fallback execution chain"""
    
    # Create an operation that fails for OpenAI but succeeds for Anthropic
    async def mock_operation(provider_name):
        if provider_name == "openai":
            raise Exception("OpenAI API Error")
        return {"content": "Fallback success", "input_tokens": 10, "output_tokens": 5, "finish_reason": "stop"}
        
    result, provider_used, chain = await fallback_manager.execute_with_fallback("openai", mock_operation)
    
    assert provider_used == "anthropic"
    assert len(chain) == 2
    assert chain[0] == "openai"
    assert chain[1] == "anthropic"
    assert result["content"] == "Fallback success"
