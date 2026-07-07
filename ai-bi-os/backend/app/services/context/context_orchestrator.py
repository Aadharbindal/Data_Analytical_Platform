from sqlalchemy.orm import Session
from app.models.context import ContextPackage, ContextHistory
from app.services.context.context_planner import ContextPlanner
from app.services.context.context_assembler import ContextAssembler
from app.services.context.context_filter import ContextFilter
from app.services.context.context_ranker import ContextRanker
from app.services.context.context_validator import ContextValidator
from app.services.context.context_compressor import ContextCompressor

class ContextOrchestrator:
    """Coordinates the deterministic building of the AI context package."""
    
    @staticmethod
    def build_context(db: Session, workspace_id: str, dataset_version_id: str, question: str, token_budget: int = 8000) -> ContextPackage:
        try:
            # 1. Create Package Container
            package = ContextPackage(
                workspace_id=workspace_id,
                dataset_version_id=dataset_version_id,
                question=question,
                token_budget=token_budget
            )
            db.add(package)
            db.flush()
            
            # 2. Plan
            plan = ContextPlanner.plan(question)
            package.inferred_intent = plan.get("intent")
            
            # 3. Assemble
            items = ContextAssembler.assemble(db, dataset_version_id, plan, package.id)
            
            # 4. Filter
            items = ContextFilter.filter_items(items)
            
            # 5. Validate
            items = ContextValidator.validate(items)
            
            # 6. Rank
            ContextRanker.rank(items, plan)
            
            # 7. Compress
            compressed_items = ContextCompressor.compress(items, token_budget)
            
            # Attach to package
            db.add_all(compressed_items)
            
            # Calculate final tokens
            package.estimated_tokens = sum(i.estimated_tokens for i in compressed_items)
            
            # History
            history = ContextHistory(
                package_id=package.id,
                action="BUILT"
            )
            db.add(history)
            
            db.commit()
            db.refresh(package)
            return package
            
        except Exception as e:
            db.rollback()
            raise e
