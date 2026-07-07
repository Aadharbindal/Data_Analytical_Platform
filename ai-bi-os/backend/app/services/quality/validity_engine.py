import pandas as pd
import re
from typing import List, Dict, Any

class ValidityEngine:
    """Validates data against inferred semantic formats (Emails, URLs, Negatives)."""
    
    @staticmethod
    def evaluate(df: pd.DataFrame, schema_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        violations = []
        invalid_count = 0
        total_evaluations = 0
        
        for col_meta in schema_metadata:
            col_name = col_meta["original_header"]
            semantic_type = col_meta.get("inferred_semantic_type")
            
            if col_name not in df.columns or not semantic_type:
                continue
                
            series = df[col_name].dropna()
            if series.empty:
                continue
                
            total_evaluations += len(series)
            
            if semantic_type == "Email":
                email_regex = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
                invalid_mask = ~series.astype(str).str.match(email_regex)
                invalids = int(invalid_mask.sum())
                if invalids > 0:
                    invalid_count += invalids
                    violations.append(ValidityEngine._create_violation(col_meta["id"], "Invalid Email Format", invalids))
                    
            elif semantic_type == "URL":
                url_regex = re.compile(r'^https?://')
                invalid_mask = ~series.astype(str).str.match(url_regex)
                invalids = int(invalid_mask.sum())
                if invalids > 0:
                    invalid_count += invalids
                    violations.append(ValidityEngine._create_violation(col_meta["id"], "Invalid URL Format", invalids))
                    
            elif semantic_type in ["Integer", "Float"] and col_meta.get("classification") == "Measure":
                # Check for unexpected negatives in measures like Revenue
                num_series = pd.to_numeric(series, errors='coerce')
                negatives = int((num_series < 0).sum())
                if negatives > 0 and col_meta.get("business_meaning") in ["Revenue", "Quantity", "Amount"]:
                    invalid_count += negatives
                    violations.append({
                        "schema_column_id": col_meta["id"],
                        "issue_category": "Business Logic Violation",
                        "severity": "Critical",
                        "priority": "P1",
                        "affected_rows_count": negatives,
                        "root_cause": f"Negative values found in measure '{col_name}'.",
                        "suggested_fix": "Review source system. Set to 0 or remove."
                    })
                    
        score = 100.0
        if total_evaluations > 0:
            score = max(0.0, 100.0 - ((invalid_count / total_evaluations) * 100))
            
        return {
            "score": round(score, 2),
            "violations": violations,
            "explanation": f"Found {invalid_count} validity violations based on semantic types."
        }
        
    @staticmethod
    def _create_violation(col_id: str, category: str, count: int):
        return {
            "schema_column_id": col_id,
            "issue_category": category,
            "severity": "High",
            "priority": "P2",
            "affected_rows_count": count,
            "root_cause": "Data does not match expected format pattern.",
            "suggested_fix": "Clean or parse data to match standard format."
        }
