from typing import Dict, Any
from app.schemas.prompt import PromptObjectResponse

class PromptSerializer:
    def __init__(self):
        pass

    def serialize(self, prompt_obj: PromptObjectResponse) -> Dict[str, Any]:
        """
        Serializes the PromptObjectResponse into a standard dictionary.
        """
        return prompt_obj.model_dump()
