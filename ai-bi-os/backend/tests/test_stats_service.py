from app.services.stats_service import (
    robust_outlier_stats,
    sample_adequacy_score,
    compute_metric_confidence,
    compute_metric_importance,
)
import numpy as np
import pandas as pd


def test_robust_outlier_stats_uses_zscore_for_symmetric_data():
    np.random.seed(0)
    data = np.append(np.random.normal(100, 10, 200), [200, 210, -50])
    result = robust_outlier_stats(pd.Series(data))
    assert result["method"] == "z_score"
    assert result["count"] >= 2


def test_robust_outlier_stats_uses_mad_for_skewed_data():
    np.random.seed(0)
    data = np.random.exponential(scale=1000, size=300)
    result = robust_outlier_stats(pd.Series(data))
    assert result["method"] == "modified_z_score_mad"


def test_robust_outlier_stats_never_crashes_on_degenerate_input():
    assert robust_outlier_stats(pd.Series([5.0] * 50))["method"] == "zero_variance"
    assert robust_outlier_stats(pd.Series([42.0]))["method"] == "insufficient_data"
    assert robust_outlier_stats(pd.Series([]))["count"] == 0


def test_sample_adequacy_score_has_no_cliff_at_bucket_boundaries():
    # n=99 vs n=100 must score nearly identically, not jump like a step function
    assert abs(sample_adequacy_score(100) - sample_adequacy_score(99)) < 1.0
    assert sample_adequacy_score(1000) == 30
    assert sample_adequacy_score(100) == 20


def test_sample_adequacy_score_is_monotonic():
    prev = -1.0
    for n in range(1, 2000, 11):
        score = sample_adequacy_score(n)
        assert score >= prev - 1e-9
        prev = score


def test_compute_metric_confidence_range():
    high = compute_metric_confidence(n=1000, coverage_pct=100, ks_p=0.5, outlier_ratio=0.0, cv=0.1)
    low = compute_metric_confidence(n=5, coverage_pct=40, ks_p=0.001, outlier_ratio=0.3, cv=3.0)
    assert high >= 90
    assert low <= 30


def test_compute_metric_importance_range():
    high = compute_metric_importance(variance_share=0.5, avg_corr=0.6, max_corr=0.8, norm_entropy=0.9, temporal_r2=0.7, temporal_significant=True)
    low = compute_metric_importance(variance_share=0.01, avg_corr=0.05, max_corr=0.1, norm_entropy=0.1)
    assert high >= 80
    assert low <= 30
