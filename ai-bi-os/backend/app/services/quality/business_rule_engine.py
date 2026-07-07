import pandas as pd
from typing import List, Dict, Any

class BusinessRuleEngine:
    """Executes dynamic business rules (e.g. Revenue >= 0)."""
    
    @staticmethod
    def evaluate(df: pd.DataFrame, schema_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        violations = []
        violations_count = 0
        total_evaluations = 0
        
        # In a real system, these would be loaded from a database BusinessRule table.
        # For Module 5, we simulate the evaluation dynamically based on schema definitions.
        
        for col_meta in schema_metadata:
            col_name = col_meta["original_header"]
            if col_name not in df.columns:
                continue
                
            series = df[col_name]
            
            # Rule 1: No negative values for specific financial measures
            if col_meta.get("business_meaning") in ["Revenue", "Amount", "Quantity", "Price", "Margin"]:
                numeric_series = pd.to_numeric(series, errors='coerce').dropna()
                if not numeric_series.empty:
                    total_evaluations += len(numeric_series)
                    negatives = int((numeric_series < 0).sum())
                    if negatives > 0:
                        violations_count += negatives
                        violations.append({
                            "schema_column_id": col_meta["id"],
                            "issue_category": "Business Rule Violation",
                            "severity": "Critical",
                            "priority": "P1",
                            "affected_rows_count": negatives,
                            "root_cause": f"{col_name} violates business rule: MUST BE >= 0",
                            "suggested_fix": "Set to 0, take absolute value, or exclude from analytics."
                        })
                        
        score = 100.0
        if total_evaluations > 0:
            score = max(0.0, 100.0 - ((violations_count / total_evaluations) * 100))
            
        return {
            "score": round(score, 2),
            "violations": violations,
            "explanation": f"Processed business rules. Found {violations_count} violations."
        }
