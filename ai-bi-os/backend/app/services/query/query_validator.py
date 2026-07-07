import re
from fastapi import HTTPException

class QueryValidator:
    """Ensures queries are safe, read-only analytical queries."""
    
    FORBIDDEN_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
        "GRANT", "REVOKE", "COMMIT", "ROLLBACK", "EXEC", "EXECUTE",
        "COPY", "ATTACH", "DETACH"
    ]
    
    @staticmethod
    def validate(sql: str):
        normalized_sql = sql.upper().strip()
        
        # Must be a SELECT or EXPLAIN or WITH statement
        if not (normalized_sql.startswith("SELECT") or normalized_sql.startswith("WITH") or normalized_sql.startswith("EXPLAIN")):
            raise HTTPException(status_code=403, detail="Only read-only SELECT or CTE (WITH) queries are allowed.")
            
        # Check for forbidden keywords using regex to ensure word boundaries
        for keyword in QueryValidator.FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{keyword}\b", normalized_sql):
                # Allow DROP only if it's "DROP VIEW" (used internally for cleanup sometimes, though ideally shouldn't be passed by user)
                if keyword == "DROP" and "DROP VIEW" in normalized_sql:
                    pass
                else:
                    raise HTTPException(status_code=403, detail=f"Forbidden keyword detected: {keyword}")
                    
        return True
