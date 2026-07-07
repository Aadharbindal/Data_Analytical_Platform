from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.schemas.context_builder import (
    ContextBuildRequest, ContextObjectCreate, ContextObjectResponse, 
    ContextValidationRequest, ContextValidationResponse
)
from app.repositories.context_repository import ContextRepository
from .context_planner import ContextPlanner
from .context_assembler import ContextAssembler
from .context_optimizer import ContextOptimizer
from .context_validator import ContextValidator
from .context_policy_engine import ContextPolicyEngine
from .context_cache import context_cache

class ContextBuilderService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ContextRepository(db)
        self.planner = ContextPlanner()
        self.assembler = ContextAssembler(db)
        self.optimizer = ContextOptimizer()
        self.validator = ContextValidator()
        self.policy_engine = ContextPolicyEngine()

    def build_context(self, request: ContextBuildRequest) -> ContextObjectResponse:
        # 1. Plan
        plan = self.planner.plan_context(request)
        
        # 2. Assemble (fetch analytics objects)
        payload, analytics_refs = self.assembler.assemble(request, plan)
        
        # 3. Apply Policies (RBAC, size limits, min confidence)
        payload = self.policy_engine.apply_policies(
            payload, 
            user_workspace=request.workspace_id,
            target_workspace=request.workspace_id
        )
        
        # 4. Optimize
        payload = self.optimizer.optimize(payload)
        
        # 5. Create in DB
        create_schema = ContextObjectCreate(
            workspace_id=request.workspace_id,
            dataset_id=request.dataset_id,
            conversation_id=request.conversation_id,
            request_id=request.request_id,
            context_purpose=plan.get("intent"),
            business_domain=request.business_domain,
            context_payload=payload
        )
        db_obj = self.repo.create(create_schema, analytics_refs)
        
        # 6. Validate Output
        response_obj = ContextObjectResponse.model_validate(db_obj)
        
        # 7. Cache
        context_cache.set_context(response_obj)
        
        return response_obj

    def get_context(self, context_id: str) -> Optional[ContextObjectResponse]:
        cached = context_cache.get_context(context_id)
        if cached:
            return cached
            
        db_obj = self.repo.get_by_id(context_id)
        if db_obj:
            response_obj = ContextObjectResponse.model_validate(db_obj)
            context_cache.set_context(response_obj)
            return response_obj
        return None

    def validate_context(self, request: ContextValidationRequest) -> ContextValidationResponse:
        context_obj = self.get_context(request.context_id)
        if not context_obj:
            return ContextValidationResponse(is_valid=False, missing_objects=["ContextObject"])
            
        return self.validator.validate_context(context_obj)

    def get_history(self) -> List[Dict[str, Any]]:
        history = self.repo.get_history()
        return [{"id": h.id, "action": h.action, "timestamp": h.timestamp} for h in history]
