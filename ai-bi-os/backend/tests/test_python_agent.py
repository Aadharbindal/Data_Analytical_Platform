import pytest
from app.services.python_agent.python_agent_service import AnalysisValidator, SandboxExecutor
from app.schemas.python_agent import WorkflowDefinitionSchema, WorkflowStepSchema
import pandas as pd
import numpy as np

def test_validator_rejects_unsafe():
    validator = AnalysisValidator()
    unsafe_def = WorkflowDefinitionSchema(
        intent="Hack",
        dataset_id="123",
        steps=[
            WorkflowStepSchema(step_id="1", operation="EVAL_CODE", parameters={"code": "import os; os.system('rm -rf /')"})
        ]
    )
    is_safe, reason = validator.validate(unsafe_def)
    assert not is_safe
    assert "not allowed" in reason

def test_validator_accepts_safe():
    validator = AnalysisValidator()
    safe_def = WorkflowDefinitionSchema(
        intent="Clean",
        dataset_id="123",
        steps=[
            WorkflowStepSchema(step_id="1", operation="DROP_NULLS", parameters={})
        ]
    )
    is_safe, reason = validator.validate(safe_def)
    assert is_safe

def test_sandbox_executor_drop_nulls():
    df = pd.DataFrame({"A": [1, 2, np.nan], "B": [4, np.nan, 6]})
    executor = SandboxExecutor()
    safe_def = WorkflowDefinitionSchema(
        intent="Clean",
        dataset_id="123",
        steps=[
            WorkflowStepSchema(step_id="1", operation="DROP_NULLS", parameters={})
        ]
    )
    results = executor.execute(df, safe_def)
    final_df = results["final_df"]
    assert len(final_df) == 1
    assert "Drop Nulls" == results["artifacts"][0]["name"]

def test_sandbox_executor_kmeans():
    df = pd.DataFrame(np.random.rand(100, 2), columns=['A', 'B'])
    executor = SandboxExecutor()
    safe_def = WorkflowDefinitionSchema(
        intent="Cluster",
        dataset_id="123",
        steps=[
            WorkflowStepSchema(step_id="1", operation="FIT_KMEANS", parameters={"n_clusters": 2, "columns": ["A", "B"]})
        ]
    )
    results = executor.execute(df, safe_def)
    final_df = results["final_df"]
    assert "cluster" in final_df.columns
    assert len(results["artifacts"]) == 1
    assert results["artifacts"][0]["type"] == "MODEL_METRICS"
