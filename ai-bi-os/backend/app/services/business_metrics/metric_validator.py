import logging
from typing import Tuple, List

logger = logging.getLogger("MetricValidator")

class MetricValidator:
    """
    Parses and validates metric formulas.
    Checks for invalid syntax, division by zero, and unsupported operations.
    """
    
    def validate_formula(self, formula: str) -> Tuple[bool, List[str]]:
        """
        MVP Validation.
        In a production system, this would build an AST (Abstract Syntax Tree) 
        and validate each token against the allowed schema and operations.
        """
        errors = []
        formula = formula.upper()
        
        # 1. Check for obvious division by zero
        if "/ 0" in formula or "/0" in formula:
            errors.append("Formula contains explicit division by zero.")
            
        # 2. Check for balanced parentheses
        if formula.count("(") != formula.count(")"):
            errors.append("Formula contains unbalanced parentheses.")
            
        # 3. Check for supported aggregation functions
        # For this engine, we require formulas to be aggregated (SUM, AVG, COUNT, etc.)
        # unless it's a simple arithmetic derivation of other aggregated metrics.
        # This is a loose check for MVP.
        supported_funcs = ["SUM", "AVG", "COUNT", "MAX", "MIN"]
        has_func = any(f in formula for f in supported_funcs)
        
        # 4. We don't strictly enforce has_func in MVP because a formula might be:
        # metric_a / metric_b
        
        is_valid = len(errors) == 0
        return is_valid, errors

metric_validator = MetricValidator()
