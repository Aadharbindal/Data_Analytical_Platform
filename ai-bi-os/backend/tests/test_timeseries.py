import pytest
from app.services.timeseries.frequency_detector import frequency_detector
from app.services.timeseries.temporal_validator import temporal_validator
from app.services.timeseries.gap_detection_engine import gap_detection_engine

def test_frequency_detector():
    """Ensure standard spacings map to correct labels."""
    
    # Hourly (~3600s)
    h_meta = {"median_delta_seconds": 3600}
    assert frequency_detector.detect_frequency(h_meta)["inferred_frequency"] == "HOURLY"
    
    # Daily (~86400s)
    d_meta = {"median_delta_seconds": 86400}
    assert frequency_detector.detect_frequency(d_meta)["inferred_frequency"] == "DAILY"

def test_temporal_validator():
    """Ensure order and duplicate flags map properly."""
    
    meta = {"is_strictly_ordered": False, "has_duplicates": True}
    res = temporal_validator.validate_time_column(meta)
    
    order = next(c for c in res if c["check_name"] == "CHRONOLOGICAL_ORDER")
    dupes = next(c for c in res if c["check_name"] == "DUPLICATES")
    
    assert order["passed"] is False
    assert dupes["passed"] is False

def test_gap_detection_engine():
    """Ensure continuity drops when gaps exist."""
    
    meta = {"missing_periods_count": 5}
    res = gap_detection_engine.analyze_gaps("DAILY", meta)
    
    assert res["continuity_score"] == 100.0 - (5 * 2.5) # 87.5
