import numpy as np
import pandas as pd
from app.services.insight_candidates import generate_candidates


def _make_dataset(seed=42, n=300):
    np.random.seed(seed)
    categories = np.random.choice(['A', 'B', 'C'], n, p=[0.6, 0.25, 0.15])
    status = [np.random.choice(['Success', 'Failed'], p=[0.7, 0.3] if c == 'A' else [0.95, 0.05]) for c in categories]
    return pd.DataFrame({
        'Category': categories,
        'Region': np.random.choice(['North', 'South', 'East', 'West'], n),
        'Revenue': np.random.exponential(1000, n),
        'Status': status,
        'Date': pd.date_range('2025-01-01', periods=n, freq='D'),
    })


SEM_DICT = {
    'business_terminology': {'primary_metric': 'Revenue', 'status_col': 'Status'},
    'semantic_dictionary': {'categorical_fields': ['Category', 'Region'], 'date_columns': ['Date']},
}


def test_generate_candidates_detects_concentration_risk_overlap():
    """Category A dominates volume (60%) AND has a much higher failure rate
    (~30% vs ~5-8% for other categories) - this must be flagged as a single
    merged finding rather than two isolated facts."""
    df = _make_dataset()
    candidates = generate_candidates(df, SEM_DICT)
    overlaps = [c for c in candidates if c['type'] == 'concentration_risk_overlap']
    assert len(overlaps) >= 1
    assert overlaps[0]['entity'] == 'A'
    assert overlaps[0]['entity_failure_pct'] > overlaps[0]['dataset_failure_pct']


def test_generate_candidates_never_crashes_on_missing_columns():
    """No status/date/categorical columns present - must degrade gracefully,
    never raise."""
    df = pd.DataFrame({'Metric1': np.random.exponential(500, 100)})
    candidates = generate_candidates(df, {})
    assert isinstance(candidates, list)


def test_generate_candidates_handles_zero_numeric_columns():
    df = pd.DataFrame({
        'Category': np.random.choice(['A', 'B'], 100),
        'Status': np.random.choice(['OK', 'Failed'], 100, p=[0.9, 0.1]),
    })
    candidates = generate_candidates(df, {})
    assert isinstance(candidates, list)


def test_generate_candidates_detects_missing_data():
    n = 200
    values = [None] * 30 + list(np.random.exponential(100, n - 30))
    np.random.shuffle(values)
    df = pd.DataFrame({
        'Category': np.random.choice(['A', 'B'], n),
        'Revenue': np.random.exponential(500, n),
        'OptionalField': values,
    })
    candidates = generate_candidates(df, {'business_terminology': {'primary_metric': 'Revenue'}, 'semantic_dictionary': {'categorical_fields': ['Category']}})
    assert any(c['type'] == 'missing_data' for c in candidates)
