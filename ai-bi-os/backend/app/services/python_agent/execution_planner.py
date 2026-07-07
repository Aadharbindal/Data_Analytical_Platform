from app.schemas.python_agent import WorkflowDefinitionSchema
from typing import Dict, Any

class ExecutionPlanner:
    def __init__(self):
        pass

    def build_plan(self, workflow_def: WorkflowDefinitionSchema) -> Dict[str, Any]:
        """
        Drafts the execution steps based on the definition.
        """
        return {
            "dataset_id": workflow_def.dataset_id,
            "steps": [step.model_dump() for step in workflow_def.steps]
        }
