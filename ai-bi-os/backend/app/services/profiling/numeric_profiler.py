import pandas as pd
import numpy as np

class NumericProfiler:
    @staticmethod
    def profile(series: pd.Series) -> dict:
        """Profiles a numeric series."""
        # Drop nulls for math
        clean_series = series.dropna()
        if clean_series.empty:
            return {}
            
        try:
            clean_series = pd.to_numeric(clean_series, errors='coerce').dropna()
        except Exception:
            return {}
            
        if clean_series.empty:
            return {}

        minimum = float(clean_series.min())
        maximum = float(clean_series.max())
        mean = float(clean_series.mean())
        median = float(clean_series.median())
        
        mode_series = clean_series.mode()
        mode = float(mode_series.iloc[0]) if not mode_series.empty else None
        
        std_dev = float(clean_series.std()) if len(clean_series) > 1 else 0.0
        variance = float(clean_series.var()) if len(clean_series) > 1 else 0.0
        range_val = float(maximum - minimum)
        sum_val = float(clean_series.sum())
        
        # Percentiles
        quantiles = clean_series.quantile([0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]).to_dict()
        q1 = quantiles.get(0.25)
        q3 = quantiles.get(0.75)
        iqr = q3 - q1 if q1 is not None and q3 is not None else None
        
        # Format percentiles for JSON
        percentiles = {str(int(k * 100)): float(v) for k, v in quantiles.items()}
        
        # CV, Skewness, Kurtosis
        cv = float(std_dev / mean) if mean and mean != 0 else None
        skewness = float(clean_series.skew()) if len(clean_series) > 2 else None
        kurtosis = float(clean_series.kurtosis()) if len(clean_series) > 3 else None
        
        # Counts
        zero_count = int((clean_series == 0).sum())
        negative_count = int((clean_series < 0).sum())
        positive_count = int((clean_series > 0).sum())
        
        return {
            "minimum": minimum,
            "maximum": maximum,
            "mean": mean,
            "median": median,
            "mode": mode,
            "std_dev": std_dev,
            "variance": variance,
            "range_val": range_val,
            "sum_val": sum_val,
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "percentiles": percentiles,
            "cv": cv,
            "skewness": skewness,
            "kurtosis": kurtosis,
            "zero_count": zero_count,
            "negative_count": negative_count,
            "positive_count": positive_count
        }
