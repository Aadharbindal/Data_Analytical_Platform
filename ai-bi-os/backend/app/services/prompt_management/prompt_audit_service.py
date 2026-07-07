from app.repositories.prompt_management_repository import PromptManagementRepository
from typing import List
from app.schemas.prompt_management import PromptHistoryResponse

class PromptAuditService:
    def __init__(self, repo: PromptManagementRepository):
        self.repo = repo

    def get_history(self) -> List[PromptHistoryResponse]:
        audits = self.repo.get_history()
        return [PromptHistoryResponse.model_validate(a) for a in audits]
