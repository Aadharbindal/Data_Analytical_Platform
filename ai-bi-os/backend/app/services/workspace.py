import uuid
from typing import Dict, Any

class WorkspaceManager:
    def __init__(self):
        # In a real app, this connects to PostgreSQL
        self.workspaces = {}

    def create_workspace(self, name: str, owner_id: str) -> Dict[str, Any]:
        workspace_id = str(uuid.uuid4())
        workspace = {
            "id": workspace_id,
            "name": name,
            "owner_id": owner_id,
            "created_at": "2026-07-05T00:00:00Z",
            "settings": {}
        }
        self.workspaces[workspace_id] = workspace
        return workspace

    def get_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        return self.workspaces.get(workspace_id)
