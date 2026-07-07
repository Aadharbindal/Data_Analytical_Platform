import pytest
from app.services.business_metrics.metric_dependency import metric_dependency
from app.services.business_metrics.metric_formula_engine import metric_formula_engine
from app.services.business_metrics.metric_validator import metric_validator
from app.services.business_metrics.metric_cache import metric_cache_manager

def test_formula_validation():
    """Test the MVP formula validator"""
    # Division by zero should fail
    is_valid, errors = metric_validator.validate_formula("SUM(sales) / 0")
    assert not is_valid
    assert len(errors) == 1
    
    # Unbalanced parentheses should fail
    is_valid, errors = metric_validator.validate_formula("(SUM(sales) + 1")
    assert not is_valid
    
    # Valid formula should pass
    is_valid, errors = metric_validator.validate_formula("SUM(sales) / COUNT(customers)")
    assert is_valid
    assert len(errors) == 0

def test_circular_dependency():
    """Test the DAG dependency resolver for circular references"""
    # A -> B -> C -> A
    
    metric_dependency.add_dependency("B", ["C"])
    metric_dependency.add_dependency("C", ["A"])
    
    # Trying to add A -> B should detect the cycle
    has_cycle = metric_dependency.check_circular("A", ["B"])
    assert has_cycle is True
    
    # Valid linear dependency should pass (D -> E)
    metric_dependency.add_dependency("E", [])
    has_cycle_2 = metric_dependency.check_circular("D", ["E"])
    assert has_cycle_2 is False

def test_formula_to_sql():
    """Test compilation of formula to SQL"""
    formula = "SUM(sales)"
    table = "dataset_v1"
    
    # Without dimension
    sql1 = metric_formula_engine.compile_to_sql(formula, table)
    assert sql1 == "SELECT SUM(sales) as value FROM dataset_v1"
    
    # With dimension
    sql2 = metric_formula_engine.compile_to_sql(formula, table, "Region")
    assert sql2 == "SELECT SUM(sales) as value, Region FROM dataset_v1 GROUP BY Region"

def test_cache_key_generation():
    """Ensure cache keys are deterministic"""
    key1 = metric_cache_manager.generate_cache_key("m1", "v1", "Region", "North", "Monthly")
    key2 = metric_cache_manager.generate_cache_key("m1", "v1", "Region", "North", "Monthly")
    key3 = metric_cache_manager.generate_cache_key("m1", "v1", "Region", "South", "Monthly")
    
    assert key1 == key2
    assert key1 != key3
