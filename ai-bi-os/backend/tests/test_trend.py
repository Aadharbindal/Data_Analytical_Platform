import pytest
from app.services.trend.trend_validator import trend_validator
from app.services.trend.trend_analyzer import trend_analyzer
from app.services.trend.growth_analyzer import growth_analyzer
from app.services.trend.change_point_detector import change_point_detector

def test_trend_validator():
    """Ensure SNR and Minimum Window are enforced."""
    
    meta = {"total_observations": 5, "signal_to_noise_ratio": 1.0}
    res = trend_validator.validate_trend_signal(meta)
    
    window = next(c for c in res if c["check_name"] == "MIN_WINDOW")
    noise = next(c for c in res if c["check_name"] == "NOISE_LEVEL")
    
    assert window["passed"] is False
    assert noise["passed"] is False

def test_trend_analyzer():
    """Ensure start/end boundaries map to trajectory."""
    
    meta = {"start_val": 100.0, "end_val": 120.0}
    res = trend_analyzer.generate_profile(meta)
    assert res["overall_trend"] == "INCREASING"

def test_growth_analyzer():
    """Ensure growth properties extract accurately."""
    
    meta = {"has_growth": True, "is_exponential": True, "growth_rate": 15.0}
    res = growth_analyzer.extract_growth_segments(meta)
    
    assert len(res) == 1
    assert res[0]["trend_type"] == "EXPONENTIAL_GROWTH"

def test_change_point_detector():
    """Ensure mock CP extraction bounds properly."""
    
    meta = {
        "change_points": [
            {"method": "CUSUM", "type": "STRUCTURAL_BREAK", "magnitude": 25.0}
        ]
    }
    res = change_point_detector.detect_change_points(meta)
    
    assert len(res) == 1
    assert res[0]["business_event_flag"] is True # magnitude > 20
