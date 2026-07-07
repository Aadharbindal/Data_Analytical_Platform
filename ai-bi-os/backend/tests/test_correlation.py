import pytest
from app.services.correlation.correlation_registry import correlation_registry
from app.services.correlation.correlation_validator import correlation_validator
from app.services.correlation.correlation_executor import correlation_executor

def test_correlation_registry():
    """Ensure registry correctly maps data types to statistical methods."""
    
    # Numeric x Numeric -> Pearson
    assert correlation_registry.determine_method("NUMERIC", "FLOAT") == "PEARSON"
    
    # Categorical x Categorical -> Cramér's V
    assert correlation_registry.determine_method("VARCHAR", "TEXT") == "CRAMERS_V"
    
    # Numeric x Categorical -> Point-Biserial
    assert correlation_registry.determine_method("INTEGER", "VARCHAR") == "POINT_BISERIAL"
    
    # Boolean x Boolean -> Phi Coefficient
    assert correlation_registry.determine_method("BOOLEAN", "BOOL") == "PHI_COEFFICIENT"

def test_correlation_validator():
    """Ensure validation correctly rejects constants and low sample sizes."""
    
    # Reject low sample size
    assert correlation_validator.validate_pair(
        {"non_null_count": 15, "distinct_count": 10},
        {"non_null_count": 15, "distinct_count": 10},
        min_sample_size=30
    ) == False
    
    # Reject constants
    assert correlation_validator.validate_pair(
        {"non_null_count": 100, "distinct_count": 1},
        {"non_null_count": 100, "distinct_count": 50},
        min_sample_size=30
    ) == False
    
    # Accept valid
    assert correlation_validator.validate_pair(
        {"non_null_count": 100, "distinct_count": 50},
        {"non_null_count": 100, "distinct_count": 50},
        min_sample_size=30
    ) == True

def test_correlation_executor_classification():
    """Ensure classification logic correctly maps coefficients to business definitions."""
    
    assert correlation_executor.classify_direction(0.95) == "Very Strong Positive"
    assert correlation_executor.classify_direction(0.75) == "Strong Positive"
    assert correlation_executor.classify_direction(0.45) == "Moderate Positive"
    assert correlation_executor.classify_direction(0.25) == "Weak Positive"
    
    assert correlation_executor.classify_direction(-0.95) == "Very Strong Negative"
    assert correlation_executor.classify_direction(-0.75) == "Strong Negative"
    
    assert correlation_executor.classify_direction(0.1) == "No Correlation"
