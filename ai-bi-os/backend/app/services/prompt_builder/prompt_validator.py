from typing import List
from app.schemas.prompt import PromptPayload, PromptValidationBase

class PromptValidator:
    def __init__(self, max_tokens: int = 100000):
        self.max_tokens = max_tokens

    def validate(self, payload: PromptPayload, estimated_tokens: int) -> List[PromptValidationBase]:
        validations = []
        if estimated_tokens > self.max_tokens:
            validations.append(PromptValidationBase(is_valid=False, validation_type="Oversized", details=f"{estimated_tokens} > {self.max_tokens}"))
            
        if not payload.evidence_context:
            validations.append(PromptValidationBase(is_valid=False, validation_type="Missing Evidence", details="Prompt lacks required evidence context"))
            
        if not validations:
            validations.append(PromptValidationBase(is_valid=True, validation_type="Structural Integrity"))
            
        return validations
