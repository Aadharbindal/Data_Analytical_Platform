import numpy as np
import pandas as pd
from app.services.analytics.correlation_engine import compute_correlation


def test_undefined_correlation_is_distinguishable_from_zero():
    """A zero-variance (constant) column has an undefined correlation, not a
    genuine zero one - the two must not be silently conflated."""
    np.random.seed(1)
    n = 50
    x = np.arange(n) + np.random.normal(0, 0.5, n)
    const = np.full(n, 5.0)
    df = pd.DataFrame({'x': x, 'const': const})
    result = compute_correlation(df)

    xc = next(r for r in result if r['x'] == 'x' and r['y'] == 'const')
    assert xc['defined'] is False
    assert xc['value'] == 0.0
    assert xc['reason'] is not None
    assert xc['p_value'] is None


def test_defined_correlation_reports_p_value():
    np.random.seed(1)
    n = 50
    x = np.arange(n) + np.random.normal(0, 0.5, n)
    y = 2 * x + np.random.normal(0, 1, n)
    df = pd.DataFrame({'x': x, 'y': y})
    result = compute_correlation(df)

    xy = next(r for r in result if r['x'] == 'x' and r['y'] == 'y')
    assert xy['defined'] is True
    assert xy['value'] > 0.9
    assert xy['p_value'] is not None
    assert xy['significant'] is True
