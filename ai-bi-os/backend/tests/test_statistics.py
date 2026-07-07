import pytest
from app.services.statistics.inference_registry import inference_registry
from app.services.statistics.inference_validator import inference_validator

def test_inference_registry_hypothesis_selection():
    """Ensure registry correctly maps assumptions to statistical tests."""
    
    # 1 Group, Normal -> One Sample T-Test
    assert inference_registry.determine_hypothesis_test(
        groups_count=1, normal=True, equal_variance=True
    ) == "ONE_SAMPLE_T_TEST"
    
    # 1 Group, Non-Normal -> Wilcoxon
    assert inference_registry.determine_hypothesis_test(
        groups_count=1, normal=False, equal_variance=True
    ) == "WILCOXON_SIGNED_RANK"
    
    # 2 Groups, Unpaired, Normal, Equal Variance -> Two Sample T-Test
    assert inference_registry.determine_hypothesis_test(
        groups_count=2, normal=True, equal_variance=True, paired=False
    ) == "TWO_SAMPLE_T_TEST_EQUAL_VAR"
    
    # 2 Groups, Unpaired, Normal, Unequal Variance -> Welch's T-Test
    assert inference_registry.determine_hypothesis_test(
        groups_count=2, normal=True, equal_variance=False, paired=False
    ) == "WELCH_T_TEST"
    
    # >2 Groups, Normal -> ANOVA
    assert inference_registry.determine_hypothesis_test(
        groups_count=3, normal=True, equal_variance=True
    ) == "ANOVA"
    
    # >2 Groups, Non-Normal -> Kruskal-Wallis
    assert inference_registry.determine_hypothesis_test(
        groups_count=3, normal=False, equal_variance=True
    ) == "KRUSKAL_WALLIS"

def test_inference_validator():
    """Ensure validation correctly interprets simple statistical moments."""
    
    # Normal data (low skew, kurtosis ~3)
    normal_stats = {"skewness": 0.1, "kurtosis": 3.0}
    assert inference_validator.check_normality(normal_stats) == True
    
    # Non-normal data (high skew)
    non_normal_stats = {"skewness": 1.5, "kurtosis": 4.0}
    assert inference_validator.check_normality(non_normal_stats) == False
    
    # Equal variance (ratio < 2)
    assert inference_validator.check_equal_variance(
        {"variance": 10}, {"variance": 15}
    ) == True
    
    # Unequal variance (ratio > 2)
    assert inference_validator.check_equal_variance(
        {"variance": 10}, {"variance": 25}
    ) == False
