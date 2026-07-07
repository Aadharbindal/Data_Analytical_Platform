from app.repositories.prompt_management_repository import PromptManagementRepository
from app.schemas.prompt_management import PromptReviewRequest, PromptApproveRequest

class PromptApprovalWorkflow:
    def __init__(self, repo: PromptManagementRepository):
        self.repo = repo

    def submit_review(self, request: PromptReviewRequest):
        version = self.repo.get_version(request.version_id)
        if not version:
            raise ValueError("Version not found")
        if version.lifecycle.status not in ["DRAFT", "REVIEW"]:
            raise ValueError("Can only review DRAFT or REVIEW versions")
            
        self.repo.create_review(request.version_id, request.reviewer_id, request.comments)

    def approve_version(self, request: PromptApproveRequest):
        version = self.repo.get_version(request.version_id)
        if not version:
            raise ValueError("Version not found")
        if version.lifecycle.status != "REVIEW":
            raise ValueError("Can only approve REVIEW versions")
            
        self.repo.approve_version(request.version_id, request.approver_id)
