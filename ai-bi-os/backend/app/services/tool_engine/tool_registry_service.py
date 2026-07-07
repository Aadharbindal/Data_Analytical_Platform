from app.repositories.tool_repository import ToolRepository
from app.schemas.tools import ToolRegistrationRequest, ToolResponse
from typing import List

class ToolRegistryService:
    def __init__(self, repo: ToolRepository):
        self.repo = repo

    def register_tool(self, request: ToolRegistrationRequest) -> ToolResponse:
        tool = self.repo.register_tool(request)
        return ToolResponse.model_validate(tool)

    def get_tool(self, tool_id: str) -> ToolResponse:
        tool = self.repo.get_tool(tool_id)
        if not tool:
            raise ValueError("Tool not found")
        return ToolResponse.model_validate(tool)
