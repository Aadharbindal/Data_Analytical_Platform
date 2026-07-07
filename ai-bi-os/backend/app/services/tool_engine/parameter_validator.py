from typing import Dict, Any
from app.models.tools import ToolDefinition

class ParameterValidator:
    def __init__(self):
        pass

    def validate_parameters(self, tool: ToolDefinition, inputs: Dict[str, Any]) -> bool:
        """
        Validates the inputs against the tool's JSON schema and parameter constraints.
        """
        # MVP: Basic check for required keys if specified in schema
        schema = tool.input_schema
        if "required" in schema:
            for req in schema["required"]:
                if req not in inputs:
                    raise ValueError(f"Missing required parameter: {req}")
        return True
