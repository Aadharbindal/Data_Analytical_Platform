import pytest
from app.services.validation.validation_rules_engine import validation_rules_engine
from app.services.validation.validation_policy_engine import validation_policy_engine
from app.services.validation.confidence_engine import confidence_engine

def test_validation_rules_engine():
    """Ensure rule bounds correctly evaluate metrics."""
    metrics = {"missing_percentage": 4.5, "r_squared": 0.85}
    
    rules = [
        {"metric_name": "missing_percentage", "operator": "LESS_THAN", "threshold_value": 5.0, "is_critical": True},
        {"metric_name": "r_squared", "operator": "GREATER_THAN", "threshold_value": 0.80, "is_critical": False}
    ]
    
    results = validation_rules_engine.evaluate_rules(metrics, rules)
    assert len(results) == 2
    assert results[0]["passed"] == True
    assert results[1]["passed"] == True
    
    # Failing rule
    failing_rules = [
        {"metric_name": "missing_percentage", "operator": "LESS_THAN", "threshold_value": 2.0, "is_critical": True}
    ]
    fail_results = validation_rules_engine.evaluate_rules(metrics, failing_rules)
    assert fail_results[0]["passed"] == False

def test_validation_policy_engine():
    """Ensure policies enforce status based on critical flags."""
    
    # Non-critical failure -> WARNING
    rule_results_warn = [{"metric_name": "r_squared", "passed": False, "is_critical": False, "actual_value": 0.7}]
    status, errs, warns = validation_policy_engine.enforce_policy(rule_results_warn)
    assert status == "WARNING"
    assert len(warns) == 1
    assert len(errs) == 0
    
    # Critical failure -> REJECTED
    rule_results_reject = [{"metric_name": "missing", "passed": False, "is_critical": True, "actual_value": 25.0}]
    status, errs, warns = validation_policy_engine.enforce_policy(rule_results_reject)
    assert status == "REJECTED"
    assert len(errs) == 1

def test_confidence_engine():
    """Ensure confidence dynamically adjusts based on metric bounds."""
    
    metrics = {"missing_percentage": 10.0, "r_squared": 0.8}
    conf = confidence_engine.calculate_confidence("REGRESSION", metrics)
    
    assert conf["data_confidence"] == 80.0 # 100 - (10*2)
    assert conf["model_confidence"] == 80.0
    assert conf["overall_confidence"] == (80 + 100 + 80) / 3.0
