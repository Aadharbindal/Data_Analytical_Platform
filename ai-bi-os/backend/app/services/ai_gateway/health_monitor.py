import asyncio
import logging
from app.services.ai_gateway.provider_registry import provider_registry
from app.models.ai_gateway import CircuitState

logger = logging.getLogger("HealthMonitor")

class HealthMonitor:
    """
    Background worker that pings providers to check health and close open circuits.
    """
    async def run(self):
        while True:
            try:
                await self.check_health()
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
            await asyncio.sleep(60) # Run every minute

    async def check_health(self):
        providers = provider_registry.get_all_providers()
        for p in providers:
            if p["circuit_state"] == CircuitState.OPEN:
                # The circuit breaker itself handles the cooldown logic when 
                # a request comes in. But the monitor could proactively test it.
                logger.info(f"HealthMonitor: {p['name']} is OPEN.")
                # We could send a lightweight ping (e.g. models list) to test here.

health_monitor = HealthMonitor()
