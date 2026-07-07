from sqlalchemy.orm import Session
from app.models.context import ContextPackage
from app.models.prompt import PromptTemplate

class PromptPlanner:
    """Selects the appropriate PromptTemplate based on intent."""
    
    @staticmethod
    def select_template(db: Session, context_package: ContextPackage) -> PromptTemplate:
        intent = context_package.inferred_intent or "GENERAL_QUERY"
        
        # Mapping intent to template name
        mapping = {
            "DIAGNOSTIC": "Root Cause Analysis",
            "PREDICTIVE": "Forecast Request",
            "PRESCRIPTIVE": "Recommendation Explanation",
            "GENERAL_QUERY": "Business Analysis"
        }
        
        target_name = mapping.get(intent, "Business Analysis")
        template = db.query(PromptTemplate).filter(PromptTemplate.name == target_name).first()
        
        # Fallback if not seeded
        if not template:
            template = PromptTemplate(
                name=target_name,
                system_template="You are an AI Business Intelligence assistant. Context: {{ context_items }}",
                user_template="Question: {{ question }}"
            )
            
        return template
