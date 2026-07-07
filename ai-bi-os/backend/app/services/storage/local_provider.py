import os
import shutil
from app.services.storage.provider import StorageProviderInterface

class LocalStorageProvider(StorageProviderInterface):
    def __init__(self, base_dir: str = "./data/catalog"):
        self.base_dir = base_dir

    def _get_full_path(self, path: str) -> str:
        full_path = os.path.join(self.base_dir, path)
        # Ensure directories exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        return full_path

    def save_file(self, content: bytes, path: str) -> str:
        """
        Saves a file to local disk under base_dir. 
        `path` should be like `workspace-123/project-456/dataset-789/v1/raw.csv`
        """
        full_path = self._get_full_path(path)
        with open(full_path, "wb") as f:
            f.write(content)
        return full_path

    def delete_file(self, path: str) -> bool:
        full_path = self._get_full_path(path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
        
    def get_file_content(self, path: str) -> bytes:
        full_path = self._get_full_path(path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")
        with open(full_path, "rb") as f:
            return f.read()
