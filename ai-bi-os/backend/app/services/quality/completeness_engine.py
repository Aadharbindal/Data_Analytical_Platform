import pandas as pd
from typing import List, Dict, Any

class CompletenessEngine:
    """Evaluates missing blocks, empty strings, and null counts."""
    
    @staticmethod
    def evaluate(df: pd.DataFrame, schema_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        violations = []
        total_rows = len(df)
        
        if total_rows == 0:
            return {"score": 0, "violations": []}
            
        total_missing = 0
        
        for col_meta in schema_metadata:
            col_name = col_meta["original_header"]
            if col_name not in df.columns:
                continue
                
            series = df[col_name]
            
            # Count nulls and empty strings
            null_count = int(series.isnull().sum())
            if series.dtype == 'object':
                empty_str_count = int((series.astype(str).str.strip() == '').sum())
                null_count += empty_str_count
                
            total_missing += null_count
            
            if null_count > 0:
                missing_pct = null_count / total_rows
                
                # Determine severity based on if column is "Identifier" or "Measure"
                severity = "Medium"
                priority = "P2"
                if col_meta.get("classification") in ["Identifier", "Measure"]:
                    if missing_pct > 0.1:
                        severity = "High"
                        priority = "P1"
                    
                violations.append({
                    "schema_column_id": col_meta["id"],
                    "issue_category": "Missing Values",
                    "severity": severity,
                    "priority": priority,
                    "affected_rows_count": null_count,
                    "root_cause": "Data entry gap or system extract failure.",
                    "suggested_fix": "Impute missing values, drop rows, or verify source extraction."
                })
                
        total_cells = total_rows * len(df.columns)
        completeness_pct = ((total_cells - total_missing) / total_cells) * 100 if total_cells > 0 else 0
        
        return {
            "score": round(completeness_pct, 2),
            "violations": violations,
            "explanation": f"{total_missing} cells missing out of {total_cells}."
        }
