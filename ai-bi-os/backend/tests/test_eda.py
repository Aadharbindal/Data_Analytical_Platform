import pytest
from app.services.eda.eda_planner import eda_planner
from app.services.eda.eda_registry import eda_registry
from app.services.eda.eda_executor import eda_executor

def test_registry():
    """Ensure registry correctly maps types to statistical operations."""
    num_analyzers = eda_registry.get_analyzers_for_type("NUMERIC")
    assert "mean" in num_analyzers
    assert "kurtosis" in num_analyzers
    
    txt_analyzers = eda_registry.get_analyzers_for_type("VARCHAR")
    assert "avg_len" in txt_analyzers
    assert "frequency_dist" in txt_analyzers

def test_planner():
    """Ensure the planner constructs the correct payload for the executor."""
    schema = [
        {"name": "revenue", "type": "NUMERIC"},
        {"name": "status", "type": "VARCHAR"}
    ]
    
    plan = eda_planner.create_execution_plan(schema)
    assert "column_level" in plan
    
    assert plan["column_level"]["revenue"]["type"] == "NUMERIC"
    assert "mean" in plan["column_level"]["revenue"]["specific"]
    
    assert plan["column_level"]["status"]["type"] == "VARCHAR"
    assert "avg_len" in plan["column_level"]["status"]["specific"]

def test_executor_distribution_inference():
    """Ensure statistical moments correctly infer the data distribution."""
    # Normal: skewness ~0, kurtosis ~3
    dist_normal = eda_executor.infer_distribution(skewness=0.1, kurtosis=3.0)
    assert dist_normal["type"] == "NORMAL"
    
    # Skewed Right: skewness > 1
    dist_right = eda_executor.infer_distribution(skewness=2.5, kurtosis=5.0)
    assert dist_right["type"] == "SKEWED_RIGHT"
    
    # Skewed Left: skewness < -1
    dist_left = eda_executor.infer_distribution(skewness=-1.8, kurtosis=4.2)
    assert dist_left["type"] == "SKEWED_LEFT"
