import pandas as pd
import numpy as np
import re
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import PlainTextResponse, HTMLResponse
from typing import Optional
from app.services.data_processing import get_active_dataset, get_dataframe
from app.core.security import get_current_user
from app.services.stats_service import compute_kpis, forecast_series

router = APIRouter()

@router.get("/kpis")
async def get_kpis_endpoint(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"kpis": [], "chart_data": []}
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        return {"kpis": [], "chart_data": []}
        
    return compute_kpis(df)

@router.get("/eda")
async def get_eda(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"columns": [], "rows": 0, "summary": []}
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
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
async def get_statistics(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"stats": []}
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
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
async def get_correlation(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"correlation": []}
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
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
async def get_distribution(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
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
async def get_outliers(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"outliers": []}
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
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
async def get_timeseries(metric: str, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
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
async def get_trend(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"trends": []}
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
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
async def get_kpi_center(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"kpis": []}
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        return {"kpis": []}

    kpi_data = compute_kpis(df).get("kpis", [])
    
    available_kpis = []
    omitted_kpis = []
    
    expected_kpis = ["Total Revenue", "Active Users", "Avg. Deal Size", "Pipeline Health"]
    for expected in expected_kpis:
        computed = next((k for k in kpi_data if k["name"] == expected), None)
        if computed:
            available_kpis.append({
                "name": expected,
                "column": computed.get("column", "Unknown"),
                "status": "Available",
                "value": computed["value"],
                "trend": computed.get("trend")
            })
        else:
            reason = "No matching column found"
            if expected == "Total Revenue": reason = "No revenue/sales/amount column found"
            elif expected == "Active Users": reason = "No customer/user column found"
            elif expected == "Avg. Deal Size": reason = "Missing deal or revenue columns"
            elif expected == "Pipeline Health": reason = "no column matching stage|status|pipeline found"
            omitted_kpis.append({"name": expected, "reason": reason})
    
    return {"available_kpis": available_kpis, "omitted_kpis": omitted_kpis}

@router.get("/forecast")
async def get_forecast(metric: str, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded")
        
    res = forecast_series(df, metric)
    return res

@router.get("/export/{page}")
async def export_csv(page: str, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded")
        
    if page == "eda":
        res = await get_eda()
        summary = res.get("summary", [])
        if not summary:
            return PlainTextResponse("No data")
        
        lines = ["column,type,min,max,mean,nulls,unique"]
        for s in summary:
            lines.append(f"{s.get('column','')},{s.get('type','')},{s.get('min','')},{s.get('max','')},{s.get('mean','')},{s.get('nulls','')},{s.get('unique','')}")
        return PlainTextResponse("\\n".join(lines))
        
    elif page == "statistics":
        res = await get_statistics()
        stats = res.get("stats", [])
        if not stats:
            return PlainTextResponse("No data")
        lines = ["column,mean,median,std,skew,kurtosis"]
        for s in stats:
            lines.append(f"{s.get('column','')},{s.get('mean','')},{s.get('median','')},{s.get('std','')},{s.get('skew','')},{s.get('kurtosis','')}")
        return PlainTextResponse("\\n".join(lines))
        
    elif page == "outliers":
        res = await get_outliers()
        outliers = res.get("outliers", [])
        if not outliers:
            return PlainTextResponse("No data")
        lines = ["column,z_score_outliers,iqr_outliers"]
        for o in outliers:
            lines.append(f"{o.get('column','')},{o.get('z_score_outliers','')},{o.get('iqr_outliers','')}")
        return PlainTextResponse("\\n".join(lines))
        
    else:
        raise HTTPException(status_code=400, detail="Invalid page for export")

@router.get("/report")
async def generate_report(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return HTMLResponse("<h1>No active dataset</h1>")
        
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        return HTMLResponse("<h1>Dataset not loaded</h1>")
        
    kpis = compute_kpis(df).get("kpis", [])
    quality = dataset_info.get("quality_score", 0)
    
    html = f"""
    <html>
    <head>
        <title>Data Report - {dataset_info['name']}</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; line-height: 1.6; color: #333; }}
            .card {{ border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
            .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }}
            .kpi-box {{ background: #f9f9f9; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #eee; }}
            .kpi-value {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
            .kpi-name {{ font-size: 14px; color: #666; }}
            h1 {{ color: #1e3a8a; }}
            h2 {{ border-bottom: 2px solid #eee; padding-bottom: 5px; }}
        </style>
    </head>
    <body>
        <h1>Data Report: {dataset_info['name']}</h1>
        <div class="card">
            <h2>Summary</h2>
            <p><strong>Rows:</strong> {len(df)}</p>
            <p><strong>Columns:</strong> {len(df.columns)}</p>
            <p><strong>Quality Score:</strong> {quality}/100</p>
        </div>
        
        <h2>Key Performance Indicators</h2>
        <div class="kpi-grid">
    """
    for kpi in kpis:
        html += f"""
            <div class="kpi-box">
                <div class="kpi-value">{kpi['value']}</div>
                <div class="kpi-name">{kpi['name']}</div>
            </div>
        """
    html += """
        </div>
        
        <div class="card" style="margin-top: 20px;">
            <h2>Top Columns (Numeric)</h2>
            <ul>
    """
    
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols[:5]:
        html += f"<li><strong>{col}:</strong> Mean = {df[col].mean():.2f}, Max = {df[col].max():.2f}</li>"
        
    html += """
            </ul>
        </div>
        <p style="text-align: center; color: #999; margin-top: 40px;">Generated by DataMind OS</p>
    </body>
    </html>
    """
    return HTMLResponse(html)

from fastapi.responses import StreamingResponse
from app.services.pdf_generator import generate_pdf_report
from datetime import datetime

@router.get("/report.pdf")
async def get_pdf_report(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")
        
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded")
        
    try:
        pdf_buffer = generate_pdf_report(dataset_info, df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
        
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_name = "".join(c for c in dataset_info["name"] if c.isalnum() or c in ('-', '_')).rstrip()
    filename = f"datamind_report_{safe_name}_{date_str}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/metrics")
async def get_metrics_explorer(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        return []

    from app.services.stats_service import find_column
    date_col = find_column(df, r'date|month|year|time')
    has_date = bool(date_col)
    
    df_temp = df.copy()
    if has_date:
        df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
        df_temp = df_temp.dropna(subset=[date_col])

    res = []
    for col in df.select_dtypes(include=[np.number]).columns:
        clean_col = df[col].dropna()
        if len(clean_col) == 0:
            continue
            
        mean = float(clean_col.mean())
        sum_val = float(clean_col.sum())
        
        sparkline = []
        if has_date and len(df_temp) > 0:
            monthly = df_temp.groupby(df_temp[date_col].dt.to_period('M'))[col].sum().reset_index()
            monthly = monthly.sort_values(date_col)
            sparkline = [float(v) for v in monthly[col].values]
            
        res.append({
            "metric": col,
            "mean": mean,
            "sum": sum_val,
            "min": float(clean_col.min()),
            "max": float(clean_col.max()),
            "sparkline": sparkline
        })
    return res

@router.get("/breakdown")
async def get_breakdown(metric: str, period: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No dataset")
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded")
        
    if metric not in df.columns:
        raise HTTPException(status_code=400, detail="Invalid metric")
        
    from app.services.stats_service import find_column
    date_col = find_column(df, r'date|month|year|time')
    
    full_df = df
    if period and date_col:
        df_temp = df.copy()
        df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
        df = df_temp[df_temp[date_col].dt.strftime('%Y-%m') == period]

    # Get categorical columns (object, string, category)
    cat_cols = df.select_dtypes(exclude=[np.number, 'datetime64']).columns
    
    breakdowns = []
    for cat in cat_cols:
        if date_col and cat == date_col:
            continue
            
        # Use full dataset to check cardinality so we don't accidentally include IDs that have few values in a specific month
        if 'id' in cat.lower() or full_df[cat].nunique() > len(full_df) * 0.5 or full_df[cat].nunique() > 50 or full_df[cat].nunique() < 2:
            continue
            
        grouped = df.groupby(cat)[metric].sum().reset_index()
        grouped = grouped.sort_values(metric, ascending=False).head(8)
        
        data_points = []
        for _, row in grouped.iterrows():
            data_points.append({"label": str(row[cat]), "value": float(row[metric])})
            
        if data_points:
            breakdowns.append({
                "dimension": cat,
                "data": data_points
            })
            
    return breakdowns

import sqlite3
from app.core.config import DB_PATH

@router.get("/confidence")
async def get_confidence(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"insights": {"verified": 0, "unverified": 0}, "recommendations": {"verified": 0, "unverified": 0}, "audit_trail": []}
        
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Insights stats
    cursor.execute('SELECT verified, count(*) as count FROM insights WHERE user_id = ? AND dataset_id = ? GROUP BY verified', (current_user["id"], dataset_info["id"]))
    ins_stats = cursor.fetchall()
    ins_verified = 0
    ins_unverified = 0
    for row in ins_stats:
        if row["verified"] == 1: ins_verified = row["count"]
        else: ins_unverified = row["count"]
        
    # Recommendations stats
    cursor.execute('SELECT verified, count(*) as count FROM recommendations WHERE user_id = ? AND dataset_id = ? GROUP BY verified', (current_user["id"], dataset_info["id"]))
    rec_stats = cursor.fetchall()
    rec_verified = 0
    rec_unverified = 0
    for row in rec_stats:
        if row["verified"] == 1: rec_verified = row["count"]
        else: rec_unverified = row["count"]
        
    # Audit trail (recent insights)
    cursor.execute('SELECT id, title, description, audit_sql, confidence, verified FROM insights WHERE user_id = ? AND dataset_id = ? ORDER BY created_at DESC LIMIT 100', (current_user["id"], dataset_info["id"]))
    audit_trail = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    
    return {
        "insights": {"verified": ins_verified, "unverified": ins_unverified},
        "recommendations": {"verified": rec_verified, "unverified": rec_unverified},
        "audit_trail": audit_trail
    }
