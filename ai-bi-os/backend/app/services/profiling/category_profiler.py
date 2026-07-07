import pandas as pd

class CategoryProfiler:
    @staticmethod
    def profile(series: pd.Series) -> dict:
        """Profiles categorical/dimension data."""
        clean_series = series.dropna()
        if clean_series.empty:
            return {}
            
        value_counts = clean_series.value_counts(normalize=True)
        
        # Get top 5 and bottom 5 (as percentages)
        top_5 = value_counts.head(5).to_dict()
        bottom_5 = value_counts.tail(5).to_dict()
        
        top_categories = {str(k): float(v) for k, v in top_5.items()}
        bottom_categories = {str(k): float(v) for k, v in bottom_5.items()}
        
        # Entropy (balance score)
        import numpy as np
        probabilities = value_counts.values
        entropy = -np.sum(probabilities * np.log2(probabilities)) if len(probabilities) > 0 else 0.0
        max_entropy = np.log2(len(probabilities)) if len(probabilities) > 0 else 1.0
        
        # Normalized entropy (0 to 1) where 1 means perfectly balanced
        category_balance_score = float(entropy / max_entropy) if max_entropy > 0 else 1.0
        
        return {
            "top_categories": top_categories,
            "bottom_categories": bottom_categories,
            "category_balance_score": category_balance_score
        }
