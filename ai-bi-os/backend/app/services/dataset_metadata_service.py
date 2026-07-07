import json
from app.services.storage.provider import StorageProviderInterface

class DatasetMetadataService:
    def __init__(self, provider: StorageProviderInterface):
        self.provider = provider

    def store_metadata(self, storage_path: str, metadata: dict) -> str:
        """
        Stores metadata as a JSON file alongside the raw file.
        `storage_path` is expected to be the path where the raw file resides.
        E.g., workspace_1/project_1/dataset_1/v1/metadata.json
        """
        import os
        base_dir = os.path.dirname(storage_path)
        metadata_path = os.path.join(base_dir, "metadata.json")
        
        content = json.dumps(metadata, indent=4).encode('utf-8')
        return self.provider.save_file(content, metadata_path)
