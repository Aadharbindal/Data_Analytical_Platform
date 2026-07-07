import os
import shutil
from typing import Optional
from app.services.storage.provider import StorageProviderInterface
from app.services.storage.local_provider import LocalStorageProvider

class StorageService:
    """
    Orchestrates chunked uploads and final dataset storage placement.
    Delegates final persistence to a StorageProvider.
    """
    def __init__(self, provider: Optional[StorageProviderInterface] = None, chunk_dir: str = "./data/chunks"):
        # Default to local provider if none injected
        self.provider = provider or LocalStorageProvider()
        self.chunk_dir = chunk_dir
        os.makedirs(self.chunk_dir, exist_ok=True)

    def save_chunk(self, job_id: str, chunk_index: int, content: bytes):
        """Temporarily store chunks locally before merging."""
        job_dir = os.path.join(self.chunk_dir, job_id)
        os.makedirs(job_dir, exist_ok=True)
        chunk_path = os.path.join(job_dir, f"chunk_{chunk_index}")
        with open(chunk_path, "wb") as f:
            f.write(content)

    def merge_chunks_to_provider(self, job_id: str, total_chunks: int, target_path: str) -> str:
        """Merges local chunks and sends the final byte stream to the provider."""
        job_dir = os.path.join(self.chunk_dir, job_id)
        
        # We merge into a temp file first to save memory instead of reading all chunks into RAM
        temp_merged_path = os.path.join(self.chunk_dir, f"{job_id}_merged.tmp")
        
        try:
            with open(temp_merged_path, "wb") as outfile:
                for i in range(total_chunks):
                    chunk_path = os.path.join(job_dir, f"chunk_{i}")
                    if not os.path.exists(chunk_path):
                        raise FileNotFoundError(f"Missing chunk {i} for job {job_id}")
                    with open(chunk_path, "rb") as infile:
                        outfile.write(infile.read())
            
            # Now upload the fully assembled temp file via the provider
            with open(temp_merged_path, "rb") as merged_file:
                final_uri = self.provider.save_file(merged_file.read(), target_path)
                
            return final_uri
        finally:
            # Cleanup temp merged file and chunks
            if os.path.exists(temp_merged_path):
                os.remove(temp_merged_path)
            shutil.rmtree(job_dir, ignore_errors=True)

    def save_direct_upload(self, target_path: str, content: bytes) -> str:
        """Bypass chunks and send directly to provider."""
        return self.provider.save_file(content, target_path)
