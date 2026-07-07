import hashlib
import os

class HashGenerator:
    @staticmethod
    def generate_file_hash(file_path: str, chunk_size: int = 8192) -> str:
        """Generates a SHA-256 hash for a given file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
