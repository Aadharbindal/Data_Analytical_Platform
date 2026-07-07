from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.repositories.prompt_management_repository import PromptManagementRepository
from app.schemas.prompt_management import (
    PromptTemplateCreate, PromptTemplateResponse,
    PromptVersionCreate, PromptVersionResponse,
    PromptReviewRequest, PromptApproveRequest,
    PromptPublishRequest, PromptRollbackRequest,
    PromptDiffResponse, PromptHistoryResponse
)
from .prompt_registry_service import PromptRegistryService
from .prompt_version_manager import PromptVersionManager
from .prompt_lifecycle_manager import PromptLifecycleManager
from .prompt_template_manager import PromptTemplateManager
from .prompt_approval_workflow import PromptApprovalWorkflow
from .prompt_diff_engine import PromptDiffEngine
from .prompt_policy_engine import PromptPolicyEngine
from .prompt_audit_service import PromptAuditService
from .prompt_management_cache import pm_cache

class PromptManagementService:
    def __init__(self, db: Session):
        self.repo = PromptManagementRepository(db)
        
        self.registry_service = PromptRegistryService(self.repo)
        self.version_manager = PromptVersionManager(self.repo)
        self.lifecycle_manager = PromptLifecycleManager(self.repo)
        self.template_manager = PromptTemplateManager()
        self.approval_workflow = PromptApprovalWorkflow(self.repo)
        self.diff_engine = PromptDiffEngine(self.repo)
        self.policy_engine = PromptPolicyEngine()
        self.audit_service = PromptAuditService(self.repo)

    def create_template(self, request: PromptTemplateCreate) -> PromptTemplateResponse:
        return self.registry_service.create_template(request)
        
    def get_templates(self, workspace_id: str) -> List[PromptTemplateResponse]:
        return self.registry_service.get_templates(workspace_id)

    def create_version(self, request: PromptVersionCreate) -> PromptVersionResponse:
        self.policy_engine.validate_policies(request)
        version = self.version_manager.create_version(request)
        pm_cache.invalidate_cache(request.template_id)
        return version

    def review_version(self, request: PromptReviewRequest):
        self.approval_workflow.submit_review(request)
        
    def approve_version(self, request: PromptApproveRequest):
        self.approval_workflow.approve_version(request)

    def publish_version(self, request: PromptPublishRequest) -> PromptVersionResponse:
        res = self.lifecycle_manager.publish_version(request)
        pm_cache.invalidate_cache(res.template_id)
        return res

    def rollback_version(self, request: PromptRollbackRequest) -> PromptVersionResponse:
        res = self.lifecycle_manager.rollback_version(request)
        pm_cache.invalidate_cache(res.template_id)
        return res

    def get_diff(self, version_id: str) -> PromptDiffResponse:
        return self.diff_engine.generate_diff(version_id)

    def get_history(self) -> List[PromptHistoryResponse]:
        return self.audit_service.get_history()
