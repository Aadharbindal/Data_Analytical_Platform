import os
import pandas as pd
from typing import Dict, Any

class MetadataManager:
    @staticmethod
    def extract_metadata(file_path: str, file_type: str) -> Dict[str, Any]:
        """Extracts basic metadata such as size and row count (if small enough)."""
        size_bytes = os.path.getsize(file_path)
        
        # We can expand this later to read row counts if needed, 
        # but for large files we should defer to background tasks.
        return {
            "file_size_bytes": size_bytes,
            "file_type": file_type
        }
