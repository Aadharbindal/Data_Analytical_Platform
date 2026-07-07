from app.schemas.prompt import PromptPayload
import json

class PromptFormatter:
    def __init__(self):
        pass

    def format_for_llm(self, payload: PromptPayload) -> str:
        """
        Takes the structured PromptPayload and serializes it into the final string
        that will be sent to the LLM (e.g. wrapped in XML tags or Markdown).
        """
        # MVP: just dump as structured JSON for the router to handle
        return payload.model_dump_json(exclude_none=True, indent=2)
