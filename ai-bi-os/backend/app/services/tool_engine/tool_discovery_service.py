from app.repositories.tool_repository import ToolRepository
from app.schemas.tools import ToolResponse
from typing import List

class ToolDiscoveryService:
    def __init__(self, repo: ToolRepository):
        self.repo = repo

    def get_all_tools(self) -> List[ToolResponse]:
        tools = self.repo.get_all_tools()
        return [ToolResponse.model_validate(t) for t in tools]
