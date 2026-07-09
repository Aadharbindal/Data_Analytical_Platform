import pandas as pd
import re
from fastapi import APIRouter
from app.services.data_processing import get_active_dataset, get_dataframe

router = APIRouter()

def find_column(df: pd.DataFrame, pattern: str) -> str:
    for col in df.columns:
        if re.search(pattern, col, re.IGNORECASE):
            return col
    return None

@router.get("/kpis")
async def get_kpis():
    dataset_info = get_active_dataset()
    if not dataset_info:
        return {"kpis": [], "chart_data": []}
    
    df = get_dataframe(dataset_info["id"])
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
    rev_col = find_column(df, r'revenue|sales|amount')
    
    # 2. Active Users / Customers
    user_col = None
    for col in df.columns:
        if re.search(r'customer|user|client|account', col, re.IGNORECASE):
            # Exclude categorical dimensions that just happen to contain the word
            if not re.search(r'region|country|state|type|category|group|segment|tier', col, re.IGNORECASE):
                user_col = col
                break
                
    # 3. Deals / Transactions
    deal_col = find_column(df, r'deal|order|transaction|invoice')
    
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
            "value": round(float(curr_rev), 2),
            "previous_value": round(float(prev_rev), 2),
            "trend": calc_trend(curr_rev, prev_rev),
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
            "value": float(curr_users),
            "previous_value": float(prev_users),
            "trend": calc_trend(curr_users, prev_users),
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
            "value": round(float(curr_avg), 2),
            "previous_value": round(float(prev_avg), 2),
            "trend": calc_trend(curr_avg, prev_avg),
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
            
        curr_health = calc_health(recent_df)
        prev_health = calc_health(prior_df) if prior_df is not None else curr_health
        
        kpis.append({
            "id": "kpi_pipeline",
            "name": "Pipeline Health",
            "value": round(curr_health, 1),
            "previous_value": round(prev_health, 1),
            "trend": calc_trend(curr_health, prev_health),
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
        except Exception:
            pass

    return {"kpis": kpis, "chart_data": chart_data}
