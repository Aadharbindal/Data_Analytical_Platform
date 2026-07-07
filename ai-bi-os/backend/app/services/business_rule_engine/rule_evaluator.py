import time
from typing import Dict, Any, List

class RuleEvaluator:
    """Safely parses and evaluates AST-based conditions against an input object."""
    
    def evaluate(self, expression_ast: Dict[str, Any], input_data: Dict[str, Any]) -> bool:
        """
        Recursively evaluate an AST expression.
        Expected AST format:
        {
            "operator": "AND" | "OR" | "NOT" | "==" | ">" | "<" | ">=" | "<=" | "!=",
            "field": "revenue" (if leaf node),
            "value": 100000 (if leaf node),
            "conditions": [...] (if logic node)
        }
        """
        operator = expression_ast.get("operator", "==")
        
        if operator in ["AND", "OR", "NOT"]:
            return self._evaluate_logic_node(expression_ast, input_data)
        else:
            return self._evaluate_leaf_node(expression_ast, input_data)
            
    def _evaluate_logic_node(self, ast: Dict[str, Any], input_data: Dict[str, Any]) -> bool:
        operator = ast.get("operator")
        conditions = ast.get("conditions", [])
        
        if operator == "AND":
            return all(self.evaluate(cond, input_data) for cond in conditions)
        elif operator == "OR":
            return any(self.evaluate(cond, input_data) for cond in conditions)
        elif operator == "NOT":
            if conditions:
                return not self.evaluate(conditions[0], input_data)
            return False
            
        return False
        
    def _evaluate_leaf_node(self, ast: Dict[str, Any], input_data: Dict[str, Any]) -> bool:
        field = ast.get("field")
        value = ast.get("value")
        operator = ast.get("operator", "==")
        
        if not field:
            return False
            
        # Safe traversal for nested fields e.g., "financials.roi"
        parts = field.split('.')
        actual_val = input_data
        for part in parts:
            if isinstance(actual_val, dict):
                actual_val = actual_val.get(part)
            else:
                return False
                
        if actual_val is None:
            return False
            
        try:
            if operator == "==":
                return actual_val == value
            elif operator == "!=":
                return actual_val != value
            elif operator == ">":
                return actual_val > value
            elif operator == "<":
                return actual_val < value
            elif operator == ">=":
                return actual_val >= value
            elif operator == "<=":
                return actual_val <= value
            else:
                return False
        except TypeError:
            return False
