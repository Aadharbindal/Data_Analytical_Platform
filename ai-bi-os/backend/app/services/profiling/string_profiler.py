import pandas as pd

class StringProfiler:
    @staticmethod
    def profile(series: pd.Series) -> dict:
        """Profiles a string series."""
        clean_series = series.dropna().astype(str)
        if clean_series.empty:
            return {}
            
        lengths = clean_series.str.len()
        
        min_length = int(lengths.min())
        max_length = int(lengths.max())
        avg_length = float(lengths.mean())
        
        # Empty string logic
        empty_string_count = int((clean_series == "").sum())
        
        # Whitespace only
        whitespace_count = int(clean_series.str.isspace().sum())
        
        # Case ratio (approximated by counting strictly upper vs strictly lower)
        is_upper = clean_series.str.isupper().sum()
        is_lower = clean_series.str.islower().sum()
        total_len = len(clean_series)
        
        uppercase_ratio = float(is_upper / total_len) if total_len > 0 else 0.0
        lowercase_ratio = float(is_lower / total_len) if total_len > 0 else 0.0
        
        # Special chars (naïve regex: not alphanumeric and not space)
        special_char_count = int(clean_series.str.contains(r'[^a-zA-Z0-9\s]', regex=True).sum())
        
        return {
            "min_length": min_length,
            "max_length": max_length,
            "avg_length": avg_length,
            "uppercase_ratio": uppercase_ratio,
            "lowercase_ratio": lowercase_ratio,
            "whitespace_count": whitespace_count,
            "empty_string_count": empty_string_count,
            "special_char_count": special_char_count
        }
