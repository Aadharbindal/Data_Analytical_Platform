import pytest
from app.services.distribution.distribution_validator import distribution_validator
from app.services.distribution.goodness_of_fit_engine import goodness_of_fit_engine
from app.services.distribution.tail_analysis_engine import tail_analysis_engine

def test_distribution_validator():
    """Ensure small samples are rejected."""
    
    # Should pass
    assert distribution_validator.validate_for_fitting({"valid_count": 35})
    
    # Should fail
    with pytest.raises(ValueError):
        distribution_validator.validate_for_fitting({"valid_count": 10})

def test_tail_analysis():
    """Ensure high kurtosis identifies heavy/fat tails."""
    
    col_stats = {"kurtosis": 5.2, "skewness": 2.5}
    tails = tail_analysis_engine.analyze_tails(col_stats)
    
    assert tails["is_heavy_tail"] == True
    assert tails["is_long_tail"] == True
    assert tails["is_fat_tail"] == True
    
    col_stats_flat = {"kurtosis": 1.5, "skewness": 0.1}
    tails_flat = tail_analysis_engine.analyze_tails(col_stats_flat)
    
    assert tails_flat["is_heavy_tail"] == False
    assert tails_flat["modality"] == "FLAT"

def test_goodness_of_fit():
    """Ensure AIC comparison correctly selects the best fit."""
    
    col_stats = {"skewness": 1.5, "mean": 0, "std_dev": 1}
    
    fits = goodness_of_fit_engine.fit_and_rank(col_stats)
    
    assert len(fits) == 2 # Because skew > 0.5 triggers Log-Normal candidate
    assert fits[0]["is_best_fit"] == True # Top ranked item is marked as best fit
    
    # Log-Normal is mocked to have lower AIC, so it should be the best fit
    assert fits[0]["distribution_type"] == "LOG_NORMAL"
