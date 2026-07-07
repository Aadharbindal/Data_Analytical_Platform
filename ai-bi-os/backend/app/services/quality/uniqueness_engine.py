import pandas as pd
from typing import List, Dict, Any

class UniquenessEngine:
    """Evaluates duplicate rows and duplicate identifiers."""
    
    @staticmethod
    def evaluate(df: pd.DataFrame, schema_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        violations = []
        total_rows = len(df)
        
        if total_rows == 0:
            return {"score": 100.0, "violations": []}
            
        # 1. Full Row Duplicates
        duplicate_rows = int(df.duplicated().sum())
        if duplicate_rows > 0:
            violations.append({
                "schema_column_id": None,
                "issue_category": "Duplicate Rows",
                "severity": "High",
                "priority": "P2",
                "affected_rows_count": duplicate_rows,
                "root_cause": "Exact duplicate rows exist across all columns.",
                "suggested_fix": "Apply distinct/drop_duplicates during cleaning."
            })
            
        # 2. Identifier Duplicates (Primary Key Candidates)
        id_duplicates = 0
        for col_meta in schema_metadata:
            if col_meta.get("is_primary_key_candidate") or col_meta.get("classification") == "Identifier":
                col_name = col_meta["original_header"]
                if col_name in df.columns:
                    dups = int(df.duplicated(subset=[col_name]).sum())
                    if dups > 0:
                        id_duplicates += dups
                        violations.append({
                            "schema_column_id": col_meta["id"],
                            "issue_category": "Duplicate Identifier",
                            "severity": "Critical",
                            "priority": "P1",
                            "affected_rows_count": dups,
                            "root_cause": "Column classified as identifier contains non-unique values.",
                            "suggested_fix": "Deduplicate by identifier or review join conditions."
                        })
                        
        total_duplicates = duplicate_rows + id_duplicates
        score = max(0.0, 100.0 - ((total_duplicates / (total_rows * 2)) * 100))
        
        return {
            "score": round(score, 2),
            "violations": violations,
            "explanation": f"Detected {duplicate_rows} duplicate rows and {id_duplicates} identifier duplicates."
        }
