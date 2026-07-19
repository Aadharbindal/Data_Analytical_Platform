import pandas as pd
import numpy as np

def compute_correlation(df: pd.DataFrame) -> list:
    if df is None:
        return []
    num_df = df.select_dtypes(include=[np.number])
    if num_df.empty:
        return []
    corr_matrix = num_df.corr().fillna(0)
    result = []
    for col1 in corr_matrix.columns:
        for col2 in corr_matrix.columns:
            result.append({'x': col1, 'y': col2, 'value': float(corr_matrix.loc[col1, col2])})
    return result
