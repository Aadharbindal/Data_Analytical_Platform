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
            logger.error("litellm is not installed; AI features are unavailable.")

            class MockMessage:
                content = ("AI features are not available on this server right now. "
                           "Please contact your administrator.")
                tool_calls = None
            return MockMessage()
        except Exception as e:
            if model != self.default_model:
                logger.warning(f"Model '{model}' failed ({e}); retrying with default model '{self.default_model}'.")
                try:
                    return self._call_model(self.default_model, messages, tools)
                except Exception as e2:
                    e = e2

            # The raw provider exception is useful in the log but must not reach
            # the end user: it carries internal detail (organisation ids, model
            # names, litellm stack text) and reads as a crash rather than as
            # something the person can act on. Map the common, recoverable
            # causes to plain guidance and keep the specifics server-side.
            logger.error(f"AI request failed on model '{model}': {e}", exc_info=True)
            detail = str(e).lower()
            if "rate limit" in detail or "ratelimit" in detail or "429" in detail:
                friendly = ("The AI service is rate-limited right now. "
                            "Please wait a few moments and ask again.")
            elif "api key" in detail or "authentication" in detail or "401" in detail:
                friendly = ("The AI service is not configured correctly. "
                            "Please check the API key in your server settings.")
            elif "timeout" in detail or "timed out" in detail:
                friendly = ("The AI service took too long to respond. "
                            "Please try again.")
            elif "context" in detail and "length" in detail:
                friendly = ("That request was too large for the AI model. "
                            "Try narrowing your question to fewer columns or rows.")
            else:
                friendly = ("The AI service is temporarily unavailable. "
                            "Please try again in a moment.")

            class MockMessage:
                content = friendly
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
