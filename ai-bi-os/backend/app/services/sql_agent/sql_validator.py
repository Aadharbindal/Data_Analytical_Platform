import re
from typing import Tuple

class SQLValidator:
    """
    CRITICAL: Validates generated SQL to ensure it is strictly read-only and safe.
    Rejects mutations and common injection vectors.
    """
    def __init__(self):
        # Unsafe keywords to block
        self.forbidden_keywords = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", 
            "EXECUTE", "GRANT", "REVOKE", "MERGE"
        ]
        
    def validate(self, sql: str) -> Tuple[bool, str]:
        upper_sql = sql.upper()
        
        for keyword in self.forbidden_keywords:
            # Check for the keyword as an isolated token
            if re.search(rf"\b{keyword}\b", upper_sql):
                return False, f"Contains forbidden keyword: {keyword}"
                
        # Basic check for semi-colons used for query stacking (injection)
        if ";" in sql.strip(";\n\r "): 
            return False, "Query stacking (multiple statements) is not allowed."
            
        return True, "Safe"
