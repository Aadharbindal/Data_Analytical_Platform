from app.repositories.prompt_management_repository import PromptManagementRepository
from app.schemas.prompt_management import PromptVersionCreate, PromptVersionResponse

class PromptVersionManager:
    def __init__(self, repo: PromptManagementRepository):
        self.repo = repo

    def calculate_next_version(self, template_id: str, is_major: bool) -> str:
        latest = self.repo.get_latest_version(template_id)
        if not latest:
            return "1.0.0" if is_major else "0.1.0"
            
        parts = latest.version_string.split(".")
        if len(parts) != 3:
            return "1.0.0"
            
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        
        if is_major:
            return f"{major + 1}.0.0"
        else:
            return f"{major}.{minor + 1}.0"

    def create_version(self, obj_in: PromptVersionCreate) -> PromptVersionResponse:
        version_string = self.calculate_next_version(obj_in.template_id, obj_in.is_major)
        version = self.repo.create_version(obj_in, version_string)
        return PromptVersionResponse.model_validate(version)
