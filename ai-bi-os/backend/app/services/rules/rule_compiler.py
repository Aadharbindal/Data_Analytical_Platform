from typing import Dict, Any

class RuleCompiler:
    """Translates rule ASTs into executable functions for the Executor."""
    
    @staticmethod
    def compile(ast: Dict[str, Any]):
        """
        Parses JSON AST into a python callable.
        AST Format example:
        {
            "operator": "AND",
            "conditions": [
                {"field": "insight.metric", "op": "==", "value": "Revenue"},
                {"field": "insight.severity", "op": "IN", "value": ["HIGH", "CRITICAL"]}
            ]
        }
        """
        def evaluate_condition(context: Dict[str, Any], condition: Dict[str, Any]) -> bool:
            if "operator" in condition:
                op = condition["operator"]
                sub_results = [evaluate_condition(context, c) for c in condition.get("conditions", [])]
                if op == "AND":
                    return all(sub_results)
                elif op == "OR":
                    return any(sub_results)
                elif op == "NOT":
                    return not sub_results[0]
                return False
                
            field = condition.get("field")
            op = condition.get("op")
            value = condition.get("value")
            
            # Resolve field value from context
            field_val = context
            for part in field.split('.'):
                if isinstance(field_val, dict):
                    field_val = field_val.get(part)
                elif hasattr(field_val, part):
                    field_val = getattr(field_val, part)
                else:
                    field_val = None
                    break
                    
            if op == "==":
                return field_val == value
            elif op == ">":
                return field_val is not None and field_val > value
            elif op == "<":
                return field_val is not None and field_val < value
            elif op == "IN":
                return field_val in value
            
            return False

        def compiled_rule(context: Dict[str, Any]) -> bool:
            return evaluate_condition(context, ast)
            
        return compiled_rule
