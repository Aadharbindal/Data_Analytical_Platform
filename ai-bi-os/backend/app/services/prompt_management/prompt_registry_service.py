from app.repositories.prompt_management_repository import PromptManagementRepository
from typing import List
from app.schemas.prompt_management import PromptTemplateCreate, PromptTemplateResponse

class PromptRegistryService:
    def __init__(self, repo: PromptManagementRepository):
        self.repo = repo

    def create_template(self, obj_in: PromptTemplateCreate) -> PromptTemplateResponse:
        template = self.repo.create_template(obj_in)
        return PromptTemplateResponse.model_validate(template)

    def get_templates(self, workspace_id: str) -> List[PromptTemplateResponse]:
        templates = self.repo.get_templates_by_workspace(workspace_id)
        return [PromptTemplateResponse.model_validate(t) for t in templates]
