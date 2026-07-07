from app.repositories.tool_repository import ToolRepository
from app.models.tools import ToolDefinition

class ToolValidator:
    def __init__(self, repo: ToolRepository):
        self.repo = repo

    def validate_tool_exists(self, tool_id_string: str) -> ToolDefinition:
        tool = self.repo.get_tool_by_id_string(tool_id_string)
        if not tool:
            raise ValueError(f"Tool {tool_id_string} is not registered.")
        if tool.status != "ACTIVE":
            raise ValueError(f"Tool {tool_id_string} is not active.")
        return tool
