import pandas as pd
import numpy as np
import logging

def generate_candidates(df: pd.DataFrame, sem_dict: dict) -> list[dict]:
    """Generates analytical candidates fully deterministically using Pandas."""
    candidates = []
    
    if df is None or len(df) == 0:
        return candidates
        
    bus_term = sem_dict.get("business_terminology", {}) if sem_dict else {}
    sem_categories = sem_dict.get("semantic_dictionary", {}) if sem_dict else {}
    
    # Auto-detect numeric metric
    metric = bus_term.get("primary_metric")
    if not metric or metric not in df.columns or not pd.api.types.is_numeric_dtype(df[metric]):
        num_metrics = sem_categories.get("numeric_metrics", [])
        if num_metrics and num_metrics[0] in df.columns and pd.api.types.is_numeric_dtype(df[num_metrics[0]]):
            metric = num_metrics[0]
        else:
            num_cols = df.select_dtypes(include=[np.number]).columns
            metric = num_cols[0] if len(num_cols) > 0 else None

    # Auto-detect categorical dimensions
    dims = sem_categories.get("categorical_fields", [])
    if not dims:
        cat_cols = df.select_dtypes(exclude=[np.number, 'datetime64']).columns
        dims = [c for c in cat_cols if 1 < df[c].nunique() <= 50]
    else:
        dims = [c for c in dims if c in df.columns and 1 < df[c].nunique() <= 50]

    # Auto-detect date columns
    date_cols = sem_categories.get("date_columns", [])
    if not date_cols:
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower() or pd.api.types.is_datetime64_any_dtype(df[col]):
                date_cols.append(col)
    else:
        date_cols = [c for c in date_cols if c in df.columns]

    status_col = bus_term.get("status_col")
    if not status_col:
        for col in df.columns:
            if 'status' in col.lower() or 'state' in col.lower() or 'result' in col.lower():
                status_col = col
                break
    
    # A. CONCENTRATION (top entity share per dimension)
    if metric and dims:
        for dim in dims:
            try:
                by = df.groupby(dim, observed=True)[metric].sum().sort_values(ascending=False)
                total = by.sum()
                if total > 0 and len(by) >= 2:
                    top_entity = str(by.index[0])
                    share = (by.iloc[0] / total) * 100
                    candidates.append({
                        "type": "concentration",
                        "dimension": dim,
                        "entity": top_entity,
                        "value": float(by.iloc[0]),
                        "share_pct": round(float(share), 2),
                        "sample_size": int((df[dim].astype(str) == top_entity).sum())
                    })
            except Exception as e:
                logging.error(f"Concentration candidate check failed for {dim}: {e}")

    # B. MoM TREND
    if metric and date_cols:
        for date_col in date_cols:
            try:
                df_dt = pd.to_datetime(df[date_col], errors='coerce')
                valid_dt = df_dt.dropna()
                if not valid_dt.empty:
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
                            break
            except Exception as e:
                logging.error(f"Trend candidate generation failed: {e}")

    # C. FAILURE RATE / UNHEALTHY STATUS
    if status_col and status_col in df.columns:
        unhealthy_regex = bus_term.get("status_unhealthy_regex", "fail|cancel|reject|decline|error")
        bad = df[status_col].astype(str).str.contains(unhealthy_regex, case=False, na=False)
        total_bad = bad.sum()
        if total_bad > 0:
            rate = total_bad / len(df)
            candidates.append({
                "type": "failure_rate",
                "dimension": status_col,
                "entity": "Failed/Unhealthy Records",
                "rate_pct": round(float(rate * 100), 1),
                "sample_size": int(total_bad)
            })

        # C2. CONCENTRATION x FAILURE overlap (cross-signal candidate) —
        # is the entity that dominates volume ALSO disproportionately prone
        # to failure? That's a single, more actionable finding than the two
        # facts reported in isolation ("your top seller is also your
        # biggest quality risk" vs. two unrelated stats).
        if metric and dims and len(df) > 0:
            dataset_bad_rate = float(bad.mean())
            for dim in dims:
                try:
                    by = df.groupby(dim, observed=True)[metric].sum().sort_values(ascending=False)
                    total = by.sum()
                    if total <= 0 or len(by) < 2:
                        continue
                    top_entity = str(by.index[0])
                    entity_mask = df[dim].astype(str) == top_entity
                    entity_n = int(entity_mask.sum())
                    if entity_n < 5:
                        continue
                    entity_bad_rate = float(bad[entity_mask].mean())
                    # Only surface this when the top entity is meaningfully
                    # worse than the dataset overall — otherwise it's noise.
                    if entity_bad_rate > 0.05 and entity_bad_rate > dataset_bad_rate * 1.5:
                        candidates.append({
                            "type": "concentration_risk_overlap",
                            "dimension": dim,
                            "entity": top_entity,
                            "share_pct": round((by.iloc[0] / total) * 100, 2),
                            "entity_failure_pct": round(entity_bad_rate * 100, 1),
                            "dataset_failure_pct": round(dataset_bad_rate * 100, 1),
                            "sample_size": entity_n
                        })
                except Exception as e:
                    logging.error(f"Concentration-risk overlap check failed for {dim}: {e}")

    # D. MISSING DATA
    for col in df.columns:
        missing = df[col].isnull().sum()
        total = len(df)
        if missing > 0:
            missing_pct = (missing / total) * 100
            if missing_pct > 5:
                candidates.append({
                    "type": "missing_data",
                    "dimension": col,
                    "entity": col,
                    "rate_pct": round(float(missing_pct), 1),
                    "sample_size": int(missing)
                })

    # E. FALLBACK / GENERAL SUMMARY CANDIDATES (Ensures any dataset produces candidates)
    if metric:
        total_val = float(df[metric].sum())
        mean_val = float(df[metric].mean())
        candidates.append({
            "type": "metric_summary",
            "dimension": metric,
            "entity": f"Total {metric}",
            "value": total_val,
            "mean_val": round(mean_val, 2),
            "sample_size": len(df)
        })

    # Record volume candidate
    candidates.append({
        "type": "record_volume",
        "dimension": "dataset",
        "entity": "Total Dataset Records",
        "value": len(df),
        "sample_size": len(df)
    })

    return candidates
