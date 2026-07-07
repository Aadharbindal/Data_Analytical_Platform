from sqlalchemy.orm import Session
from app.models.context import ContextPackage
from app.models.prompt import PromptPackage, PromptAudit, PromptScore
from app.services.prompts.prompt_planner import PromptPlanner
from app.services.prompts.prompt_optimizer import PromptOptimizer
from app.services.prompts.prompt_builder import PromptBuilder
from app.services.prompts.prompt_policy_engine import PromptPolicyEngine
from app.services.prompts.prompt_validator import PromptValidator

class PromptOrchestrator:
    """Coordinates the deterministic building of the Prompt Package."""
    
    @staticmethod
    def build_prompt(db: Session, context_package_id: str) -> PromptPackage:
        try:
            # 1. Load Context
            context_package = db.query(ContextPackage).filter(ContextPackage.id == context_package_id).first()
            if not context_package:
                raise ValueError("ContextPackage not found")
                
            # 2. Plan (Select Template)
            template = PromptPlanner.select_template(db, context_package)
            
            # 3. Optimize Context for Prompting
            PromptOptimizer.optimize(context_package)
            
            # 4. Build (Render Jinja2)
            prompt_package = PromptBuilder.build(context_package, template)
            
            # 5. Policy Check
            PromptPolicyEngine.check_policies(db, prompt_package)
            
            # 6. Validate
            PromptValidator.validate(prompt_package)
            
            # 7. Audit & Score
            prompt_package.audit = PromptAudit(triggered_by="SYSTEM")
            prompt_package.score = PromptScore(
                quality_score=0.9,
                expected_cost=prompt_package.estimated_tokens * 0.00001
            )
            
            db.add(prompt_package)
            db.commit()
            db.refresh(prompt_package)
            return prompt_package
            
        except Exception as e:
            db.rollback()
            raise e
