import pandas as pd
import numpy as np
from scipy import stats as scipy_stats


def compute_correlation(df: pd.DataFrame) -> list:
    if df is None:
        return []
    num_df = df.select_dtypes(include=[np.number])
    if num_df.empty:
        return []

    corr_matrix = num_df.corr()
    result = []
    for col1 in corr_matrix.columns:
        for col2 in corr_matrix.columns:
            raw_value = corr_matrix.loc[col1, col2]
            is_defined = bool(pd.notna(raw_value))

            p_value = None
            significant = False
            if is_defined:
                if col1 == col2:
                    p_value = 0.0
                    significant = True
                else:
                    pair = num_df[[col1, col2]].dropna()
                    if len(pair) >= 3:
                        try:
                            _, p_value = scipy_stats.pearsonr(pair[col1], pair[col2])
                            p_value = float(p_value) if np.isfinite(p_value) else None
                            significant = p_value is not None and p_value < 0.05
                        except Exception:
                            p_value = None

            result.append({
                'x': col1,
                'y': col2,
                # An undefined correlation (e.g. col has zero variance) is reported
                # as 0 here so existing numeric consumers keep working, but it is
                # now distinguishable from a genuine zero correlation via `defined`/
                # `reason` instead of being silently conflated with one.
                'value': float(raw_value) if is_defined else 0.0,
                'defined': is_defined,
                'reason': None if is_defined else 'zero_variance_or_insufficient_data',
                'p_value': p_value,
                'significant': significant
            })
    return result
