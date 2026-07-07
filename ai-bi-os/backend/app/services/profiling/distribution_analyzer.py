import pandas as pd
import numpy as np

class DistributionAnalyzer:
    @staticmethod
    def profile(series: pd.Series) -> dict:
        """Analyzes distribution types (Normal, Bimodal, etc.) using simple heuristics."""
        clean_series = pd.to_numeric(series, errors='coerce').dropna()
        if clean_series.empty or len(clean_series) < 10:
            return {}
            
        # Simplified Normality Test (Using skewness and kurtosis heuristic instead of heavy scipy stats)
        skew = clean_series.skew()
        kurtosis = clean_series.kurtosis()
        
        distribution_type = "Unknown"
        confidence_score = 0.5
        
        if abs(skew) < 0.5 and abs(kurtosis) < 1.0:
            distribution_type = "Normal"
            confidence_score = 0.8
        elif skew > 1.0:
            distribution_type = "Log-normal / Right Skewed"
            confidence_score = 0.7
        elif skew < -1.0:
            distribution_type = "Left Skewed"
            confidence_score = 0.7
            
        # Histogram Bins (UI Metadata)
        # Using numpy histogram to get edges and counts
        counts, bin_edges = np.histogram(clean_series, bins=10)
        
        histogram_bins = {
            "counts": [int(c) for c in counts],
            "bin_edges": [float(e) for e in bin_edges]
        }
        
        return {
            "distribution_type": distribution_type,
            "confidence_score": confidence_score,
            "histogram_bins": histogram_bins
        }
