from abc import ABC, abstractmethod

class StorageProviderInterface(ABC):
    @abstractmethod
    def save_file(self, content: bytes, path: str) -> str:
        """Saves a file and returns the final storage path/URI."""
        pass

    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """Deletes a file."""
        pass
        
    @abstractmethod
    def get_file_content(self, path: str) -> bytes:
        """Retrieves a file's content."""
        pass
