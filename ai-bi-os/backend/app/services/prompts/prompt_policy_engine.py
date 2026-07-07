from sqlalchemy.orm import Session
from app.models.prompt import PromptPackage, PromptPolicy

class PromptPolicyEngine:
    """Checks the assembled prompt against enterprise constraints."""
    
    @staticmethod
    def check_policies(db: Session, package: PromptPackage) -> None:
        # Example: Fetch global active policy
        policy = db.query(PromptPolicy).filter(PromptPolicy.is_active == True).first()
        if not policy:
            return
            
        # Enforce max tokens
        if policy.max_tokens and package.estimated_tokens > policy.max_tokens:
            raise ValueError(f"Prompt size {package.estimated_tokens} exceeds policy limit {policy.max_tokens}.")
