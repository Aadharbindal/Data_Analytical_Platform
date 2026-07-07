from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.schemas.prompt import (
    PromptBuildRequest, PromptObjectCreate, PromptObjectResponse, 
    PromptValidationRequest, PromptReferenceBase, PromptOptimizationRequest
)
from app.repositories.prompt_repository import PromptRepository
from .prompt_planner import PromptPlanner
from .prompt_composer import PromptComposer
from .prompt_optimizer import PromptOptimizer
from .prompt_validator import PromptValidator
from .prompt_formatter import PromptFormatter
from .prompt_metadata_service import PromptMetadataService
from .prompt_cache import prompt_cache

class PromptService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PromptRepository(db)
        self.planner = PromptPlanner()
        self.composer = PromptComposer(db)
        self.optimizer = PromptOptimizer(max_tokens=100000)
        self.validator = PromptValidator(max_tokens=100000)
        self.formatter = PromptFormatter()
        self.metadata_service = PromptMetadataService()

    def build_prompt(self, request: PromptBuildRequest) -> PromptObjectResponse:
        # 1. Fetch metadata
        workspace_meta = self.metadata_service.get_workspace_metadata(request.workspace_id)
        
        # 2. Plan
        plan = self.planner.plan(request)
        
        # 3. Compose (Fetches deterministic Context and Evidence)
        ctx, evd = self.composer.fetch_dependencies(request.context_id, request.evidence_id)
        payload, sections = self.composer.compose(plan, ctx, evd, request.user_request)
        
        # 4. Optimize
        payload, opt = self.optimizer.optimize(payload)
        
        # 5. Validate
        estimated_tokens = self.optimizer.estimate_tokens(payload.model_dump_json())
        validations = self.validator.validate(payload, estimated_tokens)
        
        # 6. References
        references = [
            PromptReferenceBase(source_type="CONTEXT_OBJECT", source_id=request.context_id),
            PromptReferenceBase(source_type="EVIDENCE_OBJECT", source_id=request.evidence_id)
        ]
        
        # 7. Overall status
        is_valid = all(v.is_valid for v in validations)
        validation_status = "VALIDATED" if is_valid else "REJECTED"
        
        # 8. Create DB Schema
        create_schema = PromptObjectCreate(
            workspace_id=request.workspace_id,
            conversation_id=request.conversation_id,
            request_id=request.request_id,
            prompt_type=request.prompt_type,
            prompt_size=opt.optimized_size,
            estimated_tokens=estimated_tokens,
            structured_prompt=payload,
            sections=sections,
            references=references,
            optimizations=opt,
            validations=validations,
            validation_status=validation_status
        )
        
        db_obj = self.repo.create(create_schema)
        response_obj = PromptObjectResponse.model_validate(db_obj)
        
        # 9. Cache
        if response_obj.validation_status == "VALIDATED":
            prompt_cache.set_prompt(response_obj)
            
        return response_obj

    def get_prompt(self, prompt_id: str) -> Optional[PromptObjectResponse]:
        cached = prompt_cache.get_prompt(prompt_id)
        if cached:
            return cached
            
        db_obj = self.repo.get_by_id(prompt_id)
        if db_obj:
            response_obj = PromptObjectResponse.model_validate(db_obj)
            prompt_cache.set_prompt(response_obj)
            return response_obj
        return None

    def validate_prompt(self, request: PromptValidationRequest) -> Dict[str, Any]:
        obj = self.get_prompt(request.prompt_id)
        if not obj:
            return {"is_valid": False, "reason": "Not found"}
        
        validations = self.validator.validate(obj.structured_prompt, obj.estimated_tokens)
        return {"validations": [v.model_dump() for v in validations]}
        
    def optimize_prompt(self, request: PromptOptimizationRequest) -> PromptObjectResponse:
        obj = self.get_prompt(request.prompt_id)
        if not obj:
            raise ValueError("Prompt not found")
            
        # In a real system, re-run optimization and save
        return obj

    def get_history(self) -> List[Dict[str, Any]]:
        history = self.repo.get_history()
        return [{"id": h.id, "action": h.action, "timestamp": h.timestamp} for h in history]
