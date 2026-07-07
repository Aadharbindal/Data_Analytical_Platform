from app.repositories.prompt_management_repository import PromptManagementRepository
from app.schemas.prompt_management import PromptPublishRequest, PromptRollbackRequest, PromptVersionResponse

class PromptLifecycleManager:
    def __init__(self, repo: PromptManagementRepository):
        self.repo = repo

    def publish_version(self, request: PromptPublishRequest) -> PromptVersionResponse:
        version = self.repo.get_version(request.version_id)
        if not version:
            raise ValueError("Version not found")
        if version.lifecycle.status != "APPROVED":
            raise ValueError("Only APPROVED versions can be published")
            
        self.repo.update_lifecycle_status(request.version_id, "PUBLISHED", request.actor_id)
        return PromptVersionResponse.model_validate(self.repo.get_version(request.version_id))

    def rollback_version(self, request: PromptRollbackRequest) -> PromptVersionResponse:
        version = self.repo.get_version(request.version_id)
        if not version:
            raise ValueError("Target version not found")
            
        rollback_target = self.repo.get_version(request.rollback_to_version_id)
        if not rollback_target:
            raise ValueError("Rollback reference not found")
            
        self.repo.update_lifecycle_status(
            request.version_id, 
            "ARCHIVED", 
            request.actor_id,
            rollback_ref=request.rollback_to_version_id
        )
        return PromptVersionResponse.model_validate(self.repo.get_version(request.version_id))
