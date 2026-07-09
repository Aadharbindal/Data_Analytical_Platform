import pandas as pd
import numpy as np
import re
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.data_processing import get_active_dataset, get_dataframe
from app.services.stats_service import compute_kpis, forecast_series

router = APIRouter()

@router.get("/kpis")
async def get_kpis_endpoint():
    dataset_info = get_active_dataset()
    if not dataset_info:
        return {"kpis": [], "chart_data": []}
    
    df = get_dataframe(dataset_info["id"])
    if df is None:
        return {"kpis": [], "chart_data": []}
        
    return compute_kpis(df)

@router.get("/eda")
async def get_eda():
    dataset_info = get_active_dataset()
    if not dataset_info:
        return {"columns": [], "rows": 0, "summary": []}
    
    df = get_dataframe(dataset_info["id"])
    if df is None:
        return {"columns": [], "rows": 0, "summary": []}

    summary = []
    for col in df.columns:
        col_type = str(df[col].dtype)
        is_num = pd.api.types.is_numeric_dtype(df[col])
        if is_num:
            summary.append({
                "column": col,
                "type": col_type,
                "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                "nulls": int(df[col].isna().sum())
            })
        else:
            top_vals = df[col].value_counts().head(5).to_dict()
            summary.append({
                "column": col,
                "type": col_type,
                "top_values": {str(k): int(v) for k, v in top_vals.items()},
                "unique": int(df[col].nunique()),
                "nulls": int(df[col].isna().sum())
            })

    return {
        "columns": df.columns.tolist(),
        "rows": len(df),
        "summary": summary
    }

@router.get("/statistics")
async def get_statistics():
    dataset_info = get_active_dataset()
    if not dataset_info:
        return {"stats": []}
    
    df = get_dataframe(dataset_info["id"])
    if df is None:
        return {"stats": []}

    import scipy.stats as st

    stats_list = []
    for col in df.select_dtypes(include=[np.number]).columns:
        clean_col = df[col].dropna()
        if len(clean_col) > 0:
            stats_list.append({
                "column": col,
                "mean": float(clean_col.mean()),
                "median": float(clean_col.median()),
                "std": float(clean_col.std()),
                "skew": float(st.skew(clean_col)),
                "kurtosis": float(st.kurtosis(clean_col))
            })
    return {"stats": stats_list}

@router.get("/correlation")
async def get_correlation():
    dataset_info = get_active_dataset()
    if not dataset_info:
        return {"correlation": []}
    
    df = get_dataframe(dataset_info["id"])
    if df is None:
        return {"correlation": []}

    num_df = df.select_dtypes(include=[np.number])
    if num_df.empty:
        return {"correlation": []}

    corr_matrix = num_df.corr().fillna(0)
    result = []
    for col1 in corr_matrix.columns:
        for col2 in corr_matrix.columns:
            result.append({
                "x": col1,
                "y": col2,
                "value": float(corr_matrix.loc[col1, col2])
            })
    return {"correlation": result}

@router.get("/distribution")
async def get_distribution():
    dataset_info = get_active_dataset()
    if not dataset_info:
        return []
    
    df = get_dataframe(dataset_info["id"])
    if df is None:
        return []

    res = []
    for col in df.select_dtypes(include=[np.number]).columns:
        clean_col = df[col].dropna()
        if len(clean_col) == 0:
            continue

        counts, bin_edges = np.histogram(clean_col, bins='auto')
        bins_res = []
        for i in range(len(counts)):
            bins_res.append({
                "bin": f"{bin_edges[i]:.2f} - {bin_edges[i+1]:.2f}",
                "count": int(counts[i])
            })
        res.append({
            "column_name": col,
            "distribution_type": "Numerical",
            "histogram": bins_res
        })
    return res

@router.get("/outliers")
async def get_outliers():
    dataset_info = get_active_dataset()
    if not dataset_info:
        return {"outliers": []}
    
    df = get_dataframe(dataset_info["id"])
    if df is None:
        return {"outliers": []}

    import scipy.stats as st

    outliers_res = []
    for col in df.select_dtypes(include=[np.number]).columns:
        clean_col = df[col].dropna()
        if len(clean_col) == 0:
            continue
        
        # Z-score
        z_scores = np.abs(st.zscore(clean_col))
        z_outliers = int((z_scores > 3).sum())
        
        # IQR
        q1 = clean_col.quantile(0.25)
        q3 = clean_col.quantile(0.75)
        iqr = q3 - q1
        iqr_outliers = int(((clean_col < (q1 - 1.5 * iqr)) | (clean_col > (q3 + 1.5 * iqr))).sum())
        
        outliers_res.append({
            "column": col,
            "z_score_outliers": z_outliers,
            "iqr_outliers": iqr_outliers
        })
    return {"outliers": outliers_res}

@router.get("/timeseries")
async def get_timeseries(metric: str):
    dataset_info = get_active_dataset()
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")
    
    df = get_dataframe(dataset_info["id"])
    if df is None or metric not in df.columns:
        raise HTTPException(status_code=400, detail="Invalid metric column")

    from app.services.stats_service import find_column
    date_col = find_column(df, r'date|month|year|time')
    if not date_col:
        raise HTTPException(status_code=400, detail="No date column found")

    df_temp = df.copy()
    df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
    df_temp = df_temp.dropna(subset=[date_col])
    
    monthly = df_temp.groupby(df_temp[date_col].dt.to_period('M'))[metric].sum().reset_index()
    monthly = monthly.sort_values(date_col)
    
    res = []
    for _, row in monthly.iterrows():
        res.append({
            "date": row[date_col].strftime('%Y-%m'),
            "value": float(row[metric])
        })
    return {"timeseries": res}

@router.get("/trend")
async def get_trend():
    dataset_info = get_active_dataset()
    if not dataset_info:
        return {"trends": []}
    
    df = get_dataframe(dataset_info["id"])
    if df is None:
        return {"trends": []}

    from app.services.stats_service import find_column
    date_col = find_column(df, r'date|month|year|time')
    if not date_col:
        return {"trends": []}

    df_temp = df.copy()
    df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
    df_temp = df_temp.dropna(subset=[date_col])

    trends_res = []
    for col in df_temp.select_dtypes(include=[np.number]).columns:
        monthly = df_temp.groupby(df_temp[date_col].dt.to_period('M'))[col].sum().reset_index()
        monthly = monthly.sort_values(date_col)
        if len(monthly) < 2:
            continue
            
        y = monthly[col].values
        x = np.arange(len(y))
        
        p = np.polyfit(x, y, 1)
        slope = p[0]
        direction = "up" if slope > 0 else ("down" if slope < 0 else "flat")
        
        # R-squared
        y_pred = np.polyval(p, x)
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        trends_res.append({
            "column": col,
            "slope": float(slope),
            "trend": direction.upper(),
            "r_value": float(r2)
        })
        
    return {"trend": trends_res}

@router.get("/kpi-center")
async def get_kpi_center():
    dataset_info = get_active_dataset()
    if not dataset_info:
        return {"kpis": []}
    
    df = get_dataframe(dataset_info["id"])
    if df is None:
        return {"kpis": []}

    from app.services.stats_service import find_column
    rev_col = find_column(df, r'revenue|sales|amount')
    user_col = None
    for col in df.columns:
        if re.search(r'customer|user|client|account', col, re.IGNORECASE):
            if not re.search(r'region|country|state|type|category|group|segment|tier', col, re.IGNORECASE):
                user_col = col
                break
    deal_col = find_column(df, r'deal|order|transaction|invoice')
    status_col = find_column(df, r'stage|status|pipeline')

    from app.services.stats_service import compute_kpis
    kpi_data = compute_kpis(df).get("kpis", [])
    
    available_kpis = []
    omitted_kpis = []
    
    # Map computed KPIs to frontend expected format
    def add_kpi(name, col, computed_name):
        if col:
            # Find matching computed kpi
            computed = next((k for k in kpi_data if k["name"] == computed_name), None)
            if computed:
                available_kpis.append({
                    "name": name,
                    "column": col,
                    "status": "Available",
                    "value": computed["value"],
                    "trend": computed.get("trend")
                })
            else:
                omitted_kpis.append({"name": name, "reason": "Computation failed"})
        else:
            reason = "No matching column found"
            if name == "Total Revenue": reason = "No revenue/sales/amount column found"
            elif name == "Active Users": reason = "No customer/user column found"
            elif name == "Avg. Deal Size": reason = "Missing deal or revenue columns"
            elif name == "Pipeline Health": reason = "no column matching stage|status|pipeline found"
            omitted_kpis.append({"name": name, "reason": reason})

    add_kpi("Total Revenue", rev_col, "Total Revenue")
    add_kpi("Active Users", user_col, "Active Users")
    add_kpi("Avg. Deal Size", deal_col if deal_col and rev_col else None, "Avg. Deal Size")
    add_kpi("Pipeline Health", status_col, "Pipeline Health")
    
    return {"available_kpis": available_kpis, "omitted_kpis": omitted_kpis}

@router.get("/forecast")
async def get_forecast(metric: str):
    dataset_info = get_active_dataset()
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")
    
    df = get_dataframe(dataset_info["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded")
        
    res = forecast_series(df, metric)
    return res

