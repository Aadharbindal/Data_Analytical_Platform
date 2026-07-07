import pandas as pd

class DateProfiler:
    @staticmethod
    def profile(series: pd.Series) -> dict:
        """Profiles datetime series."""
        try:
            clean_series = pd.to_datetime(series, errors='coerce').dropna()
        except Exception:
            return {}
            
        if clean_series.empty:
            return {}
            
        earliest_date = clean_series.min()
        latest_date = clean_series.max()
        
        # Range in days
        date_range_days = (latest_date - earliest_date).days if pd.notnull(earliest_date) and pd.notnull(latest_date) else 0
        
        # Weekend ratio
        weekends = clean_series.dt.dayofweek >= 5
        weekend_ratio = float(weekends.mean())
        
        # Monthly dist
        monthly_counts = clean_series.dt.month.value_counts(normalize=True).to_dict()
        monthly_distribution = {str(k): float(v) for k, v in monthly_counts.items()}
        
        # Yearly dist
        yearly_counts = clean_series.dt.year.value_counts(normalize=True).to_dict()
        year_distribution = {str(k): float(v) for k, v in yearly_counts.items()}
        
        return {
            "earliest_date": earliest_date.isoformat() if pd.notnull(earliest_date) else None,
            "latest_date": latest_date.isoformat() if pd.notnull(latest_date) else None,
            "date_range_days": int(date_range_days),
            "weekend_ratio": weekend_ratio,
            "monthly_distribution": monthly_distribution,
            "year_distribution": year_distribution
        }
