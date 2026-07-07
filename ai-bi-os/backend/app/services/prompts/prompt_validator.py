from app.models.prompt import PromptPackage, PromptValidation

class PromptValidator:
    """Verifies formatting and token limits."""
    
    @staticmethod
    def validate(package: PromptPackage) -> None:
        is_valid = True
        reasons = []
        
        if not package.system_prompt or not package.system_prompt.strip():
            is_valid = False
            reasons.append("System prompt is empty.")
            
        if not package.user_prompt or not package.user_prompt.strip():
            is_valid = False
            reasons.append("User prompt is empty.")
            
        validation = PromptValidation(
            is_valid=is_valid,
            failure_reasons=reasons
        )
        package.validation = validation
        
        if not is_valid:
            raise ValueError(f"Prompt Validation Failed: {reasons}")
