import pytest
from app.services.outlier.outlier_validator import outlier_validator
from app.services.outlier.threshold_engine import threshold_engine
from app.services.outlier.extreme_value_analyzer import extreme_value_analyzer
from app.services.outlier.business_rule_filter import business_rule_filter

def test_outlier_validator():
    """Ensure small samples are rejected."""
    
    # Should pass
    assert outlier_validator.validate_for_detection({"valid_count": 15})
    
    # Should fail
    with pytest.raises(ValueError):
        outlier_validator.validate_for_detection({"valid_count": 5})

def test_threshold_engine():
    """Ensure bounds are correctly derived."""
    
    # IQR
    col_stats_iqr = {"q1": 10.0, "q3": 20.0, "multiplier": 1.5}
    lower, upper = threshold_engine.calculate_bounds("IQR", col_stats_iqr)
    # IQR = 10, Lower = 10 - 15 = -5, Upper = 20 + 15 = 35
    assert lower == -5.0
    assert upper == 35.0
    
    # Z-Score
    col_stats_z = {"mean": 50.0, "std_dev": 5.0, "multiplier": 3.0}
    lower, upper = threshold_engine.calculate_bounds("Z_SCORE", col_stats_z)
    assert lower == 35.0
    assert upper == 65.0

def test_extreme_value_analyzer():
    """Ensure EVT limits extract the right subset."""
    col_stats = {"p99_9": 100.0, "p00_1": 0.0}
    raw = [-5.0, 10.0, 50.0, 95.0, 105.0]
    
    extremes = extreme_value_analyzer.extract_extreme_values(col_stats, raw)
    assert len(extremes) == 2
    assert extremes[0]["value"] == -5.0
    assert extremes[0]["extreme_type"] == "EXTREME_LOW"
    assert extremes[1]["value"] == 105.0
    assert extremes[1]["extreme_type"] == "EXTREME_HIGH"

def test_business_rule_filter():
    """Ensure severity cascades correctly based on std dev distance."""
    
    col_stats = {"std_dev": 2.0}
    
    # 6 std dev (12 dist) -> CRITICAL
    crit_info = business_rule_filter.assess_severity({"distance_from_mean": 12.0}, col_stats)
    assert crit_info["severity"] == "CRITICAL"
    
    # 2 std dev (4 dist) -> LOW
    low_info = business_rule_filter.assess_severity({"distance_from_mean": 4.0}, col_stats)
    assert low_info["severity"] == "LOW"
