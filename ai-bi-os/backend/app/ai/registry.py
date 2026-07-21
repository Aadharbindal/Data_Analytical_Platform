from typing import Dict, Any, Optional

import os
import logging
from app.core.config import LLM_MODEL

logger = logging.getLogger("AI-BI-OS-ModelRegistry")

class ModelRegistry:
    """Central gateway for all LLM calls, handling routing and fallback via LiteLLM."""

    def __init__(self):
        self.default_model = LLM_MODEL

    def _call_model(self, model: str, messages: list, tools: list = None):
        import litellm

        kwargs = {
            "model": model,
            "messages": messages,
        }

        if model.startswith("groq/"):
            kwargs["api_key"] = os.getenv("GROQ_API_KEY")
        else:
            kwargs["api_key"] = os.getenv("XAI_API_KEY")
        if tools:
            kwargs["tools"] = tools

        response = litellm.completion(**kwargs)
        return response.choices[0].message

    def route_request(self, messages: list, tools: list = None, target_model: str = None) -> Any:
        """
        Routes the prompt to the specified model via litellm. Returns the
        litellm message object.

        If a non-default target_model fails (larger models occasionally emit
        a malformed tool-call the provider rejects, e.g. Groq's
        "tool_use_failed" on llama-3.3-70b-versatile), this automatically
        retries once against the default model instead of surfacing the
        failure - the complex-tier model is a pure quality upgrade on top of
        the default, never a new source of failure.
        """
        model = target_model if target_model else self.default_model

        try:
            return self._call_model(model, messages, tools)
        except ImportError:
            class MockMessage:
                content = "[SYSTEM: `litellm` is not installed. Run `pip install litellm` in the backend.]"
                tool_calls = None
            return MockMessage()
        except Exception as e:
            if model != self.default_model:
                logger.warning(f"Model '{model}' failed ({e}); retrying with default model '{self.default_model}'.")
                try:
                    return self._call_model(self.default_model, messages, tools)
                except Exception as e2:
                    e = e2

            class MockMessage:
                content = f"[SYSTEM ERROR: AI Request failed. Ensure your API key is set in .env. Details: {str(e)}]"
                tool_calls = None
            return MockMessage()

class CostTracker:
    """Tracks token usage and cost per user/workspace."""
    
    def __init__(self):
        self.usage_db = []

    def log_usage(self, workspace_id: str, user_id: str, model: str, prompt_tokens: int, completion_tokens: int):
        """Logs the usage for billing purposes."""
        self.usage_db.append({
            "workspace": workspace_id,
            "user": user_id,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        })
