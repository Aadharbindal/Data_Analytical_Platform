import os
import pandas as pd
from fastapi import HTTPException
from app.services.hash_generator import HashGenerator
from app.services.metadata_manager import MetadataManager

class UploadService:
    SUPPORTED_EXTENSIONS = {".csv", ".json", ".parquet", ".xlsx"}
    MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1 GB

    @classmethod
    def validate_file_metadata(cls, filename: str, file_size: int):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension: {ext}. Supported: {cls.SUPPORTED_EXTENSIONS}")
        if file_size == 0:
            raise ValueError("File is empty.")
        if file_size > cls.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds limit of {cls.MAX_FILE_SIZE / (1024*1024)} MB")

    @classmethod
    def validate_file_content(cls, file_path: str, ext: str):
        """Perform deep validation of the file content."""
        try:
            if ext == ".csv":
                # Check encoding and malformed CSV by reading a chunk
                pd.read_csv(file_path, nrows=5)
            elif ext == ".json":
                pd.read_json(file_path, orient='records', lines=True, chunksize=5) # Assuming JSON lines or similar for large files. Or try/except json load
                # For simplicity, if it's small, load it.
                if os.path.getsize(file_path) < 10*1024*1024:
                     pd.read_json(file_path)
            elif ext == ".parquet":
                pd.read_parquet(file_path)
            elif ext == ".xlsx":
                pd.read_excel(file_path, nrows=5)
        except UnicodeDecodeError:
            raise ValueError("Invalid file encoding. Please ensure the file is UTF-8 encoded.")
        except Exception as e:
            raise ValueError(f"Malformed file content: {str(e)}")

    @classmethod
    def process_completed_upload(cls, file_path: str, filename: str):
        """Called by background worker once upload is physically complete."""
        ext = os.path.splitext(filename)[1].lower()
        file_size = os.path.getsize(file_path)
        
        # 1. Validate File Size/Ext
        cls.validate_file_metadata(filename, file_size)
        
        # 2. Validate Content (Encoding, Parsing)
        cls.validate_file_content(file_path, ext)
        
        # 3. Generate Hash
        file_hash = HashGenerator.generate_file_hash(file_path)
        
        # 4. Extract Metadata
        metadata = MetadataManager.extract_metadata(file_path, ext.strip('.'))
        
        return {
            "file_hash": file_hash,
            "metadata": metadata,
            "ext": ext.strip('.')
        }
