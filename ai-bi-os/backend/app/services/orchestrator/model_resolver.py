from app.schemas.orchestrator import ModelResolution

class ModelResolver:
    def __init__(self):
        pass

    def select_model(self, intent: str, requires_reasoning: bool = False) -> ModelResolution:
        if requires_reasoning or intent in ["Root Cause Analysis", "SQL Query"]:
            return ModelResolution(
                provider="anthropic",
                model_name="claude-3-5-sonnet-20240620",
                context_window=200000,
                capabilities=["reasoning", "coding"]
            )
        else:
            return ModelResolution(
                provider="openai",
                model_name="gpt-4o-mini",
                context_window=128000,
                capabilities=["fast", "cheap"]
            )
