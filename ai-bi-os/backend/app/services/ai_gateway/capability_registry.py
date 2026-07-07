from typing import Dict, List, Optional
from app.models.ai_gateway import TaskType

# Mapping Task Type to Default and Fallback models
_TASK_MAPPINGS = {
    TaskType.CHAT: {"default": "gpt-4o-mini", "fallback": "claude-3-haiku"},
    TaskType.REASONING: {"default": "gpt-4o", "fallback": "claude-3-5-sonnet"},
    TaskType.SQL_GENERATION: {"default": "gpt-4o", "fallback": "deepseek-chat"},
    TaskType.SUMMARIZATION: {"default": "gpt-4o-mini", "fallback": "gemini-1.5-flash"},
    TaskType.EXECUTIVE_REPORT: {"default": "claude-3-5-sonnet", "fallback": "gpt-4o"},
    TaskType.CLASSIFICATION: {"default": "gpt-3.5-turbo", "fallback": "mixtral-8x7b"},
    TaskType.EXTRACTION: {"default": "gpt-4o-mini", "fallback": "claude-3-haiku"},
    TaskType.TRANSLATION: {"default": "gemini-1.5-flash", "fallback": "gpt-4o-mini"},
    TaskType.FORECAST_EXPLANATION: {"default": "claude-3-5-sonnet", "fallback": "gpt-4o"},
    TaskType.ROOT_CAUSE: {"default": "gpt-4o", "fallback": "claude-3-5-sonnet"},
    TaskType.GENERIC: {"default": "gpt-4o-mini", "fallback": "claude-3-haiku"}
}

class CapabilityRegistry:
    def __init__(self):
        self._mappings = _TASK_MAPPINGS
        
    def get_preferred_models_for_task(self, task: TaskType) -> Dict[str, str]:
        return self._mappings.get(task, self._mappings[TaskType.GENERIC])
        
capability_registry = CapabilityRegistry()
