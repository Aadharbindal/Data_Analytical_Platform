import pandas as pd
import numpy as np
import logging

def generate_candidates(df: pd.DataFrame, sem_dict: dict) -> list[dict]:
    """Generates analytical candidates fully deterministically using Pandas."""
    candidates = []
    
    if df is None or len(df) == 0:
        return candidates
        
    bus_term = sem_dict.get("business_terminology", {})
    sem_categories = sem_dict.get("semantic_dictionary", {})
    
    metric = bus_term.get("primary_metric")
    if not metric or metric not in df.columns or not pd.api.types.is_numeric_dtype(df[metric]):
        num_metrics = sem_categories.get("numeric_metrics", [])
        metric = num_metrics[0] if num_metrics and num_metrics[0] in df.columns else None

    dims = sem_categories.get("categorical_fields", [])
    date_cols = sem_categories.get("date_columns", [])
    status_col = bus_term.get("status_col")
    
    # A. CONCENTRATION (top entity share per dimension)
    if metric:
        for dim in dims:
            if dim not in df.columns: continue
            if df[dim].nunique() > 50: continue # Skip high cardinality
            
            by = df.groupby(dim)[metric].sum().sort_values(ascending=False)
            total = by.sum()
            if total > 0 and len(by) >= 2:
                top_entity = by.index[0]
                share = (by.iloc[0] / total) * 100
                if share > 15: # Arbitrary threshold for interesting concentration
                    candidates.append({
                        "type": "concentration",
                        "dimension": dim,
                        "entity": str(top_entity),
                        "value": float(by.iloc[0]),
                        "share_pct": round(float(share), 2),
                        "sample_size": int((df[dim] == top_entity).sum())
                    })
                    
    # B. MoM TREND
    if metric and date_cols:
        date_col = date_cols[0]
        if date_col in df.columns:
            try:
                df_dt = pd.to_datetime(df[date_col], errors='coerce')
                valid_dt = df_dt.dropna()
                if not valid_dt.empty:
                    # Group by YYYY-MM
                    df_trend = df.assign(_ym=valid_dt.dt.strftime('%Y-%m'))
                    monthly = df_trend.groupby('_ym')[metric].sum()
                    if len(monthly) >= 2:
                        val_last = monthly.iloc[-1]
                        val_prev = monthly.iloc[-2]
                        if val_prev > 0:
                            mom = ((val_last - val_prev) / val_prev) * 100
                            candidates.append({
                                "type": "trend",
                                "dimension": date_col,
                                "period": str(monthly.index[-1]),
                                "value": float(val_last),
                                "mom_pct": round(float(mom), 1),
                                "sample_size": int(df_trend['_ym'].value_counts().get(monthly.index[-1], 0))
                            })
            except Exception as e:
                logging.error(f"Trend generation failed: {e}")

    # C. FAILURE RATE
    if status_col and status_col in df.columns:
        unhealthy_regex = bus_term.get("status_unhealthy_regex", "fail|cancel|reject")
        bad = df[status_col].astype(str).str.contains(unhealthy_regex, case=False, na=False)
        for dim in dims:
            if dim not in df.columns: continue
            if df[dim].nunique() > 50: continue
            
            rates = df.assign(_bad=bad).groupby(dim)["_bad"].agg(["mean", "count"])
            worst = rates[rates["count"] >= 10].sort_values("mean", ascending=False)
            if len(worst) > 0:
                rate = worst["mean"].iloc[0]
                if rate > 0.05: # > 5% failure
                    candidates.append({
                        "type": "failure_rate",
                        "dimension": dim,
                        "entity": str(worst.index[0]),
                        "rate_pct": round(float(rate * 100), 1),
                        "sample_size": int(worst["count"].iloc[0])
                    })
                    
    # D. MISSING DATA
    for col in df.columns:
        missing = df[col].isnull().sum()
        total = len(df)
        if missing > 0:
            missing_pct = (missing / total) * 100
            if missing_pct > 10:
                candidates.append({
                    "type": "missing_data",
                    "dimension": col,
                    "entity": col,
                    "rate_pct": round(float(missing_pct), 1),
                    "sample_size": int(missing)
                })

    return candidates
