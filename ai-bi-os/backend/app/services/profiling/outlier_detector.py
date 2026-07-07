import pandas as pd
import numpy as np

class OutlierDetector:
    @staticmethod
    def detect(series: pd.Series) -> dict:
        """Detects outliers using IQR and Z-Score."""
        clean_series = pd.to_numeric(series, errors='coerce').dropna()
        if clean_series.empty or len(clean_series) < 4:
            return {}
            
        # 1. IQR Method
        q1 = clean_series.quantile(0.25)
        q3 = clean_series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        iqr_outliers = clean_series[(clean_series < lower_bound) | (clean_series > upper_bound)]
        iqr_outlier_count = len(iqr_outliers)
        
        # 2. Z-Score Method
        mean = clean_series.mean()
        std = clean_series.std()
        
        zscore_outlier_count = 0
        if std and std > 0:
            z_scores = (clean_series - mean) / std
            zscore_outliers = clean_series[np.abs(z_scores) > 3]
            zscore_outlier_count = len(zscore_outliers)
            
        total_len = len(clean_series)
        outlier_percentage = float(max(iqr_outlier_count, zscore_outlier_count) / total_len) if total_len > 0 else 0.0
        
        return {
            "iqr_outlier_count": iqr_outlier_count,
            "zscore_outlier_count": zscore_outlier_count,
            "outlier_percentage": outlier_percentage
        }
