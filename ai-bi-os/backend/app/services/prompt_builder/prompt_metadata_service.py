from typing import Dict, Any

class PromptMetadataService:
    def __init__(self):
        pass

    def get_workspace_metadata(self, workspace_id: str) -> Dict[str, Any]:
        return {
            "workspace_id": workspace_id,
            "region": "US-EAST",
            "timezone": "UTC"
        }
