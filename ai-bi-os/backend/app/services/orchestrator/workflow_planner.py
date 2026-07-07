from app.schemas.orchestrator import ExecutionPlanPayload, ExecutionStepSchema

class WorkflowPlanner:
    def __init__(self):
        pass

    def build_plan(self, intent: str, workspace_id: str) -> ExecutionPlanPayload:
        steps = [
            ExecutionStepSchema(step_name="Detect Intent", step_order=1, status="COMPLETED"),
            ExecutionStepSchema(step_name="Build Context", step_order=2, status="PENDING"),
            ExecutionStepSchema(step_name="Resolve Evidence", step_order=3, status="PENDING"),
            ExecutionStepSchema(step_name="Resolve Prompt", step_order=4, status="PENDING"),
            ExecutionStepSchema(step_name="Select Agent", step_order=5, status="PENDING"),
            ExecutionStepSchema(step_name="Select Model", step_order=6, status="PENDING"),
            ExecutionStepSchema(step_name="Execute", step_order=7, status="PENDING"),
            ExecutionStepSchema(step_name="Validate Output", step_order=8, status="PENDING")
        ]
        
        return ExecutionPlanPayload(
            required_context={"workspace_id": workspace_id, "depth": "standard"},
            required_evidence={"strictness": "high"},
            required_prompt={"type": intent},
            required_tools=["sql_executor"] if intent == "SQL Query" else [],
            output_format="markdown",
            steps=steps
        )
