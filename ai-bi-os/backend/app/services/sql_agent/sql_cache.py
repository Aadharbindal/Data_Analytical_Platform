import hashlib

class SQLCache:
    def __init__(self):
        pass

    def generate_hash(self, sql: str, workspace_id: str) -> str:
        payload = f"{workspace_id}:{sql}"
        return hashlib.sha256(payload.encode()).hexdigest()
