import re

class KPIValidator:
    """Validates KPI formulas for syntax and basic rules."""
    
    @staticmethod
    def validate_formula(formula: str) -> None:
        if not formula or not formula.strip():
            raise ValueError("Formula cannot be empty.")
            
        # Basic check for matched parentheses
        if formula.count('(') != formula.count(')'):
            raise ValueError("Mismatched parentheses in formula.")
            
        # Basic check for potentially dangerous SQL injections (since we translate to DuckDB SQL)
        forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'GRANT', 'REVOKE', 'EXEC']
        upper_formula = formula.upper()
        for kw in forbidden_keywords:
            if re.search(rf"\b{kw}\b", upper_formula):
                raise ValueError(f"Forbidden keyword '{kw}' detected in formula.")
                
        # Basic check for division by zero risk statically
        if "/ 0" in formula.replace(" ", ""):
            raise ValueError("Explicit division by zero detected in formula.")
