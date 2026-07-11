import pandas as pd
import numpy as np
import re

def find_column(df: pd.DataFrame, pattern: str, numeric_only: bool = False) -> str:
    cols_to_check = df.select_dtypes(include=[np.number]).columns if numeric_only else df.columns
    for col in cols_to_check:
        if re.search(pattern, col, re.IGNORECASE):
            return col
    return None

def compute_kpis(df: pd.DataFrame) -> dict:
    if df is None:
        return {"kpis": [], "chart_data": []}
        
    kpis = []
    
    def safe_divide(a, b):
        return a / b if b else 0.0

    def calc_trend(current, previous):
        if previous == 0 or pd.isna(previous):
            return 0.0
        return round(((current - previous) / previous) * 100, 1)
    
    # 1. Total Revenue
    rev_col = find_column(df, r'revenue|sales|amount|\bmrr\b|\barr\b|turnover|income|earnings|\bgmv\b|sales_amount|order_value|net_revenue|total_revenue', numeric_only=True)
    
    # 2. Active Users / Customers
    user_col = None
    for col in df.select_dtypes(include=[np.number]).columns:
        if re.search(r'customer|user|client|account', col, re.IGNORECASE):
            # Exclude categorical dimensions that just happen to contain the word
            if not re.search(r'region|country|state|type|category|group|segment|tier', col, re.IGNORECASE):
                user_col = col
                break
                
    # 3. Deals / Transactions
    deal_candidates = []
    for col in df.select_dtypes(include=[np.number]).columns:
        if re.search(r'deal|order|transaction|invoice', col, re.IGNORECASE):
            if not re.search(r'date|month|year|time', col, re.IGNORECASE) and not pd.core.dtypes.common.is_datetime64_any_dtype(df[col]):
                deal_candidates.append(col)
                
    deal_col = None
    if deal_candidates:
        id_candidates = [c for c in deal_candidates if re.search(r'id|number|no|code', c, re.IGNORECASE)]
        if id_candidates:
            deal_col = id_candidates[0]
        else:
            deal_col = deal_candidates[0]
    
    # 4. Pipeline / Status
    status_col = find_column(df, r'stage|status|pipeline')
    
    # Date column
    date_col = find_column(df, r'date|month|year|time')
    
    if date_col:
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col])
            df = df.sort_values(by=date_col)
        except Exception:
            date_col = None

    recent_df = df
    prior_df = None
    
    if date_col:
        try:
            periods = df.groupby(df[date_col].dt.to_period('M'))
            if len(periods) >= 2:
                sorted_periods = sorted(periods.groups.keys())
                recent_df = periods.get_group(sorted_periods[-1])
                prior_df = periods.get_group(sorted_periods[-2])
        except Exception:
            pass

    # 1. KPI: Total Revenue
    if rev_col and pd.api.types.is_numeric_dtype(df[rev_col]):
        curr_rev = recent_df[rev_col].sum()
        prev_rev = prior_df[rev_col].sum() if prior_df is not None else curr_rev
        kpis.append({
            "id": "kpi_rev",
            "name": "Total Revenue",
            "column": rev_col,
            "value": round(float(curr_rev), 2),
            "previous_value": round(float(prev_rev), 2),
            "trend": calc_trend(curr_rev, prev_rev),
            "type": "currency",
            "history": []
        })

    # 2. KPI: Active Users
    if user_col:
        if pd.api.types.is_numeric_dtype(df[user_col]) and not re.search(r'id\b', user_col, re.IGNORECASE):
            curr_users = recent_df[user_col].sum()
            prev_users = prior_df[user_col].sum() if prior_df is not None else curr_users
        else:
            curr_users = recent_df[user_col].nunique()
            prev_users = prior_df[user_col].nunique() if prior_df is not None else curr_users
            
        kpis.append({
            "id": "kpi_users",
            "name": "Active Users",
            "column": user_col,
            "value": float(curr_users),
            "previous_value": float(prev_users),
            "trend": calc_trend(curr_users, prev_users),
            "type": "count",
            "history": []
        })

    # 3. KPI: Avg. Deal Size
    if rev_col and pd.api.types.is_numeric_dtype(df[rev_col]):
        curr_rev = recent_df[rev_col].sum()
        prev_rev = prior_df[rev_col].sum() if prior_df is not None else curr_rev
        
        if deal_col:
            if pd.api.types.is_numeric_dtype(df[deal_col]) and not re.search(r'id\b', deal_col, re.IGNORECASE):
                curr_deals = recent_df[deal_col].sum()
                prev_deals = prior_df[deal_col].sum() if prior_df is not None else curr_deals
            else:
                curr_deals = recent_df[deal_col].nunique()
                prev_deals = prior_df[deal_col].nunique() if prior_df is not None else curr_deals
        else:
            curr_deals = len(recent_df)
            prev_deals = len(prior_df) if prior_df is not None else curr_deals
            
        curr_avg = safe_divide(curr_rev, curr_deals)
        prev_avg = safe_divide(prev_rev, prev_deals)
        
        kpis.append({
            "id": "kpi_deal_size",
            "name": "Avg. Deal Size",
            "column": deal_col if deal_col else "(Row Count)",
            "value": round(float(curr_avg), 2),
            "previous_value": round(float(prev_avg), 2),
            "trend": calc_trend(curr_avg, prev_avg),
            "type": "currency",
            "history": []
        })

    # 4. KPI: Pipeline Health
    if status_col:
        def calc_health(df_subset):
            if df_subset.empty:
                return 0.0
            s = df_subset[status_col].astype(str)
            healthy = s.str.contains(r'won|active|open|closed', case=False, na=False)
            unhealthy = s.str.contains(r'lost|churn|cancel|reject|fail', case=False, na=False)
            mask = healthy & ~unhealthy
            return float(mask.mean() * 100)
            
        s_full = df[status_col].astype(str)
        healthy_total = s_full.str.contains(r'won|active|open|closed', case=False, na=False).sum()
        unhealthy_total = s_full.str.contains(r'lost|churn|cancel|reject|fail', case=False, na=False).sum()
        
        if healthy_total > 0 or unhealthy_total > 0:
            total_matches = healthy_total + unhealthy_total
            if total_matches >= len(df) * 0.05:
                curr_health = calc_health(recent_df)
                prev_health = calc_health(prior_df) if prior_df is not None else curr_health
            
            kpis.append({
                "id": "kpi_pipeline",
                "name": "Pipeline Health",
                "column": status_col,
                "value": round(curr_health, 1),
                "previous_value": round(prev_health, 1),
                "trend": calc_trend(curr_health, prev_health),
                "type": "percent",
                "history": []
            })

    chart_data = []
    if date_col and rev_col and pd.api.types.is_numeric_dtype(df[rev_col]):
        try:
            monthly_rev = df.groupby(df[date_col].dt.strftime('%b %Y'))[rev_col].sum().reset_index()
            monthly_rev['temp_date'] = pd.to_datetime(monthly_rev[date_col], format='%b %Y')
            monthly_rev = monthly_rev.sort_values(by='temp_date')
            for _, row in monthly_rev.iterrows():
                chart_data.append({
                    "name": row[date_col],
                    "value": round(float(row[rev_col]), 2)
                })
                
            fc = forecast_series(df, rev_col, periods=2)
            if fc.get("available"):
                if chart_data:
                    chart_data[-1]["forecast"] = chart_data[-1]["value"]
                for f_point in fc.get("forecast", []):
                    chart_data.append({
                        "name": f_point["date"],
                        "value": None,
                        "forecast": round(f_point["forecast"], 2)
                    })
        except Exception:
            pass
            
    # Populate history for KPIs based on date_col grouping if possible
    if date_col:
        try:
            df_temp = df.dropna(subset=[date_col]).copy()
            periods_list = df_temp.groupby(df_temp[date_col].dt.to_period('M'))
            
            for k in kpis:
                hist = []
                # Sort periods chronologically
                sorted_p = sorted(periods_list.groups.keys())
                for p in sorted_p:
                    group_df = periods_list.get_group(p)
                    val = 0.0
                    
                    if k["id"] == "kpi_rev" and rev_col and pd.api.types.is_numeric_dtype(group_df[rev_col]):
                        val = group_df[rev_col].sum()
                        
                    elif k["id"] == "kpi_users" and user_col:
                        if pd.api.types.is_numeric_dtype(group_df[user_col]) and not re.search(r'id\b', user_col, re.IGNORECASE):
                            val = group_df[user_col].sum()
                        else:
                            val = group_df[user_col].nunique()
                            
                    elif k["id"] == "kpi_deal_size":
                        r = group_df[rev_col].sum() if (rev_col and pd.api.types.is_numeric_dtype(group_df[rev_col])) else 0.0
                        if deal_col:
                            if pd.api.types.is_numeric_dtype(group_df[deal_col]) and not re.search(r'id\b', deal_col, re.IGNORECASE):
                                d = group_df[deal_col].sum()
                            else:
                                d = group_df[deal_col].nunique()
                        else:
                            d = len(group_df)
                        val = safe_divide(r, d)
                        
                    elif k["id"] == "kpi_pipeline" and status_col:
                        val = calc_health(group_df)
                        
                    hist.append({"date": p.strftime('%b %Y'), "value": round(float(val), 2)})
                
                k["history"] = hist
        except Exception:
            pass

    return {"kpis": kpis, "chart_data": chart_data}


def quality_report(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {"quality_score": 0, "breakdown": {"completeness": 0, "uniqueness": 0, "type_consistency": 0, "validity": 0}}
        
    completeness = (1 - df.isna().mean().mean()) * 100
    
    # Uniqueness (simplified to row duplication ratio)
    dup_ratio = df.duplicated().mean()
    uniqueness = (1 - dup_ratio) * 100
    
    # Type consistency (percent of columns with single inferred type)
    # For a simple mock, we'll give 100% minus 5% for each object column that has mixed types.
    type_consistency = 100.0
    for col in df.columns:
        if df[col].dtype == 'object':
            types = df[col].dropna().map(type).nunique()
            if types > 1:
                type_consistency -= 5.0
    type_consistency = max(0.0, type_consistency)
    
    # Validity (are numeric values within expected ranges? - mock)
    validity = 100.0
    
    score = (completeness + uniqueness + type_consistency + validity) / 4
    
    return {
        "quality_score": float(score),
        "breakdown": {
            "completeness": float(completeness),
            "uniqueness": float(uniqueness),
            "type_consistency": float(type_consistency),
            "validity": float(validity)
        }
    }

def forecast_series(df: pd.DataFrame, metric_col: str, periods: int = 3) -> dict:
    if df.empty:
        return {"available": False, "reason": "Empty dataset"}
        
    actual_col = next((c for c in df.columns if c.lower() == metric_col.lower()), None)
    if not actual_col or not pd.api.types.is_numeric_dtype(df[actual_col]):
        return {"available": False, "reason": "Invalid metric column"}
        
    metric_col = actual_col
        
    date_col = find_column(df, r'date|month|year|time')
    if not date_col:
         return {"available": False, "reason": "No date column found"}
         
    df_temp = df.copy()
    df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
    df_temp = df_temp.dropna(subset=[date_col])
    
    monthly = df_temp.groupby(df_temp[date_col].dt.to_period('M'))[metric_col].sum().reset_index()
    monthly = monthly.sort_values(date_col)
    
    if len(monthly) < 4:
        return {"available": False, "reason": "Not enough history (need at least 4 periods)"}
        
    import numpy as np
    y = monthly[metric_col].values
    x = np.arange(len(y))
    
    p, cov = np.polyfit(x, y, 1, cov=True)
    m = p[0]
    b = p[1]
    
    y_pred = m * x + b
    residuals = y - y_pred
    sse = np.sum(residuals**2)
    df_err = len(x) - 2
    mse = sse / df_err if df_err > 0 else 0
    std_err = np.sqrt(mse)
    
    t_val = 1.96
    forecast_values = []
    last_date = monthly[date_col].iloc[-1]
    
    x_mean = np.mean(x)
    ssx = np.sum((x - x_mean)**2)
    
    for i in range(1, periods + 1):
        fx = len(x) - 1 + i
        fy = m * fx + b
        
        # Avoid division by zero in ssx
        moe = 0
        if ssx > 0:
            moe = t_val * std_err * np.sqrt(1 + 1/len(x) + (fx - x_mean)**2 / ssx)
        else:
            moe = t_val * std_err
            
        next_month = last_date + i
        lower = max(0, fy - moe)
        upper = fy + moe
        
        forecast_values.append({
            "date": next_month.strftime('%b %Y'),
            "forecast": float(fy),
            "lower": float(lower),
            "upper": float(upper)
        })
        
    historical_values = []
    for _, row in monthly.iterrows():
        historical_values.append({
            "date": row[date_col].strftime('%b %Y'),
            "value": float(row[metric_col])
        })
        
    return {
        "available": True,
        "method": "Linear trend projection",
        "historical": historical_values,
        "forecast": forecast_values
    }
