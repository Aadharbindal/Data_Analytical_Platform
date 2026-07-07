import pandas as pd
from typing import List, Dict, Any

class ConsistencyEngine:
    """Evaluates mixed casing, whitespaces, and format consistencies."""
    
    @staticmethod
    def evaluate(df: pd.DataFrame, schema_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        violations = []
        inconsistencies = 0
        total_checks = 0
        
        for col_meta in schema_metadata:
            col_name = col_meta["original_header"]
            if col_name not in df.columns:
                continue
                
            series = df[col_name].dropna()
            if series.empty:
                continue
                
            # String Consistency Checks
            if series.dtype == 'object':
                str_series = series.astype(str)
                total_checks += len(series)
                
                # Check 1: Leading/Trailing Whitespace
                whitespace_mask = str_series.str.match(r'^\s+|\s+$')
                ws_count = int(whitespace_mask.sum())
                if ws_count > 0:
                    inconsistencies += ws_count
                    violations.append({
                        "schema_column_id": col_meta["id"],
                        "issue_category": "Whitespace Inconsistency",
                        "severity": "Low",
                        "priority": "P3",
                        "affected_rows_count": ws_count,
                        "root_cause": "Leading or trailing spaces detected.",
                        "suggested_fix": "Apply .strip() during data cleaning."
                    })
                
                # Check 2: Mixed Casing in Dimension (if categorical)
                if col_meta.get("classification") == "Dimension":
                    # Check if we have 'Apple' and 'apple'
                    lower_counts = str_series.str.lower().nunique()
                    raw_counts = str_series.nunique()
                    if raw_counts > lower_counts:
                        diff = raw_counts - lower_counts
                        inconsistencies += diff * 10 # heuristic penalty
                        violations.append({
                            "schema_column_id": col_meta["id"],
                            "issue_category": "Mixed Casing",
                            "severity": "Medium",
                            "priority": "P2",
                            "affected_rows_count": diff,
                            "root_cause": "Same categorical value represented in different cases.",
                            "suggested_fix": "Normalize to lowercase or title case."
                        })
                        
        score = 100.0
        if total_checks > 0:
            penalty = (inconsistencies / total_checks) * 100
            score = max(0.0, 100.0 - penalty)
            
        return {
            "score": round(score, 2),
            "violations": violations,
            "explanation": "Evaluated textual format consistency across dimensions."
        }
