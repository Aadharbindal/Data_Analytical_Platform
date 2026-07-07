from typing import Dict, Any
from app.schemas.context_builder import ContextObjectResponse

class ContextSerializer:
    def __init__(self):
        pass

    def serialize(self, context_obj: ContextObjectResponse) -> Dict[str, Any]:
        """
        Serializes the ContextObject into a standard dictionary.
        """
        return context_obj.model_dump()
