from app.repositories.prompt_management_repository import PromptManagementRepository
from app.models.prompt_management import PromptDiff
from app.schemas.prompt_management import PromptDiffResponse

class PromptDiffEngine:
    def __init__(self, repo: PromptManagementRepository):
        self.repo = repo

    def generate_diff(self, version_id: str) -> PromptDiffResponse:
        version = self.repo.get_version(version_id)
        if not version:
            raise ValueError("Version not found")
            
        existing_diff = self.repo.get_diff(version_id)
        if existing_diff:
            return PromptDiffResponse.model_validate(existing_diff)
            
        # MVP Mock diff calculation
        added = ["System Section"]
        removed = []
        modified = []
        delta = version.estimated_tokens
        
        if version.parent_version_id:
            parent = self.repo.get_version(version.parent_version_id)
            if parent:
                delta = version.estimated_tokens - parent.estimated_tokens
                modified.append("Content")

        diff = PromptDiff(
            version_id=version_id,
            added_sections=added,
            removed_sections=removed,
            modified_sections=modified,
            token_delta=delta
        )
        self.repo.save_diff(diff)
        
        return PromptDiffResponse.model_validate(diff)
