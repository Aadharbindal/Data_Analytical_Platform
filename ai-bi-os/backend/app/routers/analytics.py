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
    
    # 1. Total Revenue
    rev_col = find_column(df, r'revenue|sales|amount')
    # 2. Active Users / Customers
    user_col = find_column(df, r'customer|user|client')
    # 3. Deals / Transactions
    deal_col = find_column(df, r'deal|order|transaction')
    # Date column
    date_col = find_column(df, r'date|month|year|time')
    
    # If date_col exists, we can try to compute trends
    if date_col:
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col])
            df = df.sort_values(by=date_col)
        except Exception:
            date_col = None

    def calc_trend(current, previous):
        if previous == 0 or pd.isna(previous):
            return 0.0
        return round(((current - previous) / previous) * 100, 1)

    def append_kpi(kpi_id, name, col, agg_func, is_unique=False):
        if not col or col not in df.columns:
            return
        
        try:
            if date_col:
                # Group by month or generic period
                periods = df.groupby(df[date_col].dt.to_period('M'))
                if len(periods) >= 2:
                    sorted_periods = sorted(periods.groups.keys())
                    recent_period = periods.get_group(sorted_periods[-1])
                    prior_period = periods.get_group(sorted_periods[-2])
                    
                    if is_unique:
                        curr_val = recent_period[col].nunique()
                        prev_val = prior_period[col].nunique()
                    else:
                        curr_val = float(recent_period[col].agg(agg_func))
                        prev_val = float(prior_period[col].agg(agg_func))
                        
                    kpis.append({
                        "id": kpi_id,
                        "name": name,
                        "value": round(curr_val, 2) if isinstance(curr_val, float) else curr_val,
                        "previous_value": round(prev_val, 2) if isinstance(prev_val, float) else prev_val,
                        "trend": calc_trend(curr_val, prev_val),
                        "history": []
                    })
                    return
        except Exception as e:
            pass
            
        # Fallback if no date column or not enough data
        if is_unique:
            val = df[col].nunique()
        else:
            val = float(df[col].agg(agg_func))
            
        kpis.append({
            "id": kpi_id,
            "name": name,
            "value": round(val, 2) if isinstance(val, float) else val,
            "previous_value": round(val, 2) if isinstance(val, float) else val,
            "trend": 0.0,
            "history": []
        })

    # Total Revenue
    if rev_col and pd.api.types.is_numeric_dtype(df[rev_col]):
        append_kpi("kpi_rev", "Total Revenue", rev_col, 'sum')
        
    # Active Users
    if user_col:
        append_kpi("kpi_users", "Active Users", user_col, 'count', is_unique=True)
        
    # Avg. Deal Size
    if rev_col and pd.api.types.is_numeric_dtype(df[rev_col]) and deal_col:
        append_kpi("kpi_deal_size", "Avg. Deal Size", rev_col, 'mean')
        
    # Pipeline Health / Deals count
    if deal_col:
        append_kpi("kpi_deals", "Total Deals", deal_col, 'count')

    chart_data = []
    if date_col and rev_col and pd.api.types.is_numeric_dtype(df[rev_col]):
        try:
            # Group by month and sum revenue
            monthly_rev = df.groupby(df[date_col].dt.strftime('%b %Y'))[rev_col].sum().reset_index()
            # Sort by date
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
