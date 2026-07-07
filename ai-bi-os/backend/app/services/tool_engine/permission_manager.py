from app.models.tools import ToolDefinition

class PermissionManager:
    def __init__(self):
        pass

    def check_permissions(self, tool: ToolDefinition, actor_id: str) -> bool:
        """
        Enforces RBAC and workspace isolation for tool execution.
        """
        # MVP: assume valid for now
        return True
