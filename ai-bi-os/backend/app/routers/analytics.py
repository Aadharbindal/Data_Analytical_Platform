import pandas as pd
import numpy as np
import re
import threading
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import PlainTextResponse, HTMLResponse
from typing import Optional
from app.services.data_processing import get_active_dataset, get_dataframe
from app.core.security import get_current_user
from app.services.stats_service import compute_kpis, compute_executive_kpis, forecast_series, robust_outlier_stats

router = APIRouter()

# ─── Result cache ──────────────────────────────────────────────────────────────
# Stores computed analytics results to avoid re-computation on repeat requests.
# Key: (user_id, dataset_id, endpoint_name)  →  computed result dict
_result_cache: dict = {}
_result_lock = threading.Lock()

def _rcache_get(key: tuple):
    with _result_lock:
        return _result_cache.get(key)

def _rcache_set(key: tuple, value) -> None:
    with _result_lock:
        _result_cache[key] = value

def invalidate_analytics_cache(user_id: str) -> None:
    """Clear all cached analytics results for a user. Called on dataset change."""
    with _result_lock:
        keys = [k for k in _result_cache if isinstance(k, tuple) and k and k[0] == user_id]
        for k in keys:
            del _result_cache[k]


@router.get("/prefetch")
async def prefetch_analytics(current_user: dict = Depends(get_current_user)):
    """
    Returns KPIs + active dataset info in a single call.
    Frontend calls this once on mount to warm all caches simultaneously.
    """
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"active_dataset": None, "kpis": {"kpis": [], "chart_data": []}}

    cache_key = (current_user["id"], dataset_info["id"], "kpis")
    kpis = _rcache_get(cache_key)
    if kpis is None:
        df = get_dataframe(dataset_info["id"], current_user["id"])
        if df is not None:
            kpis = compute_kpis(df, dataset_info.get("semantic_dict"))
            _rcache_set(cache_key, kpis)
        else:
            kpis = {"kpis": [], "chart_data": []}

    return {
        "active_dataset": {
            "id": dataset_info["id"],
            "name": dataset_info["name"],
            "row_count": dataset_info["latest_version"].get("row_count") if dataset_info.get("latest_version") else None,
            "columns": dataset_info["columns"],
            "quality_score": dataset_info.get("quality_score", 0),
            "domain": dataset_info.get("domain", "generic"),
        },
        "kpis": kpis,
    }


@router.get("/kpis")
async def get_kpis_endpoint(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"kpis": [], "chart_data": []}

    cache_key = (current_user["id"], dataset_info["id"], "kpis")
    cached = _rcache_get(cache_key)
    if cached is not None:
        return cached

    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        return {"kpis": [], "chart_data": []}

    result = compute_kpis(df, dataset_info.get("semantic_dict"))
    _rcache_set(cache_key, result)
    return result



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

@router.get("/eda/column/{column_name}")
async def get_eda_column(column_name: str, current_user: dict = Depends(get_current_user)):
    try:
        dataset_info = get_active_dataset(current_user["id"])
        if not dataset_info:
            raise HTTPException(status_code=404, detail="No active dataset")
        
        df = get_dataframe(dataset_info["id"], current_user["id"])
        if df is None:
            raise HTTPException(status_code=404, detail="Dataframe not found")
            
        if column_name not in df.columns:
            raise HTTPException(status_code=404, detail=f"Column {column_name} not found")
            
        import scipy.stats as st
        
        col_data = df[column_name]
        col_type = str(col_data.dtype)
        is_num = pd.api.types.is_numeric_dtype(col_data)
        
        null_count = int(col_data.isna().sum())
        total_count = len(col_data)
        
        if is_num:
            clean_col = col_data.dropna()
            if len(clean_col) == 0:
                return {"type": "numeric", "error": "No valid data"}
                
            # Histogram data
            counts, bin_edges = np.histogram(clean_col, bins='auto')
            histogram = [{"bin_start": float(bin_edges[i]), "bin_end": float(bin_edges[i+1]), "count": int(counts[i])} for i in range(len(counts))]
            
            # Stats
            stats = {
                "min": float(clean_col.min()),
                "max": float(clean_col.max()),
                "mean": float(clean_col.mean()),
                "median": float(clean_col.median()),
                "std": float(clean_col.std()) if len(clean_col) > 1 else 0,
                "q1": float(clean_col.quantile(0.25)),
                "q3": float(clean_col.quantile(0.75)),
                "skewness": float(st.skew(clean_col)),
                "kurtosis": float(st.kurtosis(clean_col)),
                "nulls": null_count,
                "total": total_count
            }
            
            return {
                "type": "numeric",
                "column": column_name,
                "histogram": histogram,
                "stats": stats
            }
        else:
            # Categorical
            val_counts = col_data.value_counts(dropna=False).head(50)
            frequencies = [{"value": str(k) if not pd.isna(k) else "null", "count": int(v)} for k, v in val_counts.items()]
            
            stats = {
                "unique": int(col_data.nunique(dropna=False)),
                "nulls": null_count,
                "total": total_count,
                "mode": str(col_data.mode().iloc[0]) if not col_data.mode().empty else "N/A"
            }
            
            return {
                "type": "categorical",
                "column": column_name,
                "frequencies": frequencies,
                "stats": stats
            }
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail={"error": str(e), "traceback": traceback.format_exc()})


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
    
    from app.services.analytics.correlation_engine import compute_correlation
    result = compute_correlation(df)
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

    outliers_res = []
    for col in df.select_dtypes(include=[np.number]).columns:
        clean_col = df[col].dropna()
        if len(clean_col) == 0:
            continue

        # Shape-aware: switches to a skew-robust method (median/MAD) instead of
        # blindly applying the mean/std Z-score, which is unreliable on skewed data.
        o_stats = robust_outlier_stats(clean_col)

        outliers_res.append({
            "column": col,
            "z_score_outliers": o_stats["count"],
            "iqr_outliers": o_stats["iqr_count"],
            "method": o_stats["method"],
            "skewness": o_stats["skewness"]
        })
    return {"outliers": outliers_res}

@router.get("/timeseries")
async def get_timeseries(metric: str = None, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded")
        
    semantic_dict = dataset_info.get("semantic_dict")
    
    if not metric:
        if semantic_dict:
            metric = semantic_dict.get("business_terminology", {}).get("primary_metric")
        if not metric:
            from app.services.stats_service import find_column
            metric = find_column(df, r'revenue|sales|amount|\bmrr\b|\barr\b|turnover|income|earnings|\bgmv\b|sales_amount|order_value|net_revenue|total_revenue', numeric_only=True)
            if not metric:
                num_cols = df.select_dtypes(include=[np.number]).columns
                if len(num_cols) > 0:
                    metric = num_cols[0]
                else:
                    raise HTTPException(status_code=400, detail="No metric column found")
    else:
        col_map = {c.lower(): c for c in df.columns}
        if metric.lower() not in col_map:
            raise HTTPException(status_code=400, detail="Invalid metric column")
        metric = col_map[metric.lower()]

    date_col = None
    if semantic_dict:
        date_cols = semantic_dict.get("semantic_dictionary", {}).get("date_columns", [])
        if date_cols and date_cols[0] in df.columns:
            date_col = date_cols[0]
            
    if not date_col:
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
            "r_value": float(r2),
            "sparkline": [float(val) for val in y]
        })
        
    return {"trend": trends_res}

@router.get("/kpi-center")
async def get_kpi_center(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"available_kpis": [], "omitted_kpis": [], "pipeline_health": {}}
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        return {"available_kpis": [], "omitted_kpis": [], "pipeline_health": {}}

    kpi_data = compute_executive_kpis(df, dataset_info.get("semantic_dict")).get("kpis", [])
    
    from app.services.stats_service import quality_report
    q_report = quality_report(df)
    
    sem_conf = 85
    if dataset_info.get("semantic_dict"):
         sem_conf = 95
         
    overall = (q_report.get("quality_score", 0) + sem_conf) / 2
    
    pipeline_health = {
        "dataset_quality": round(q_report.get("quality_score", 0), 1),
        "completeness": round(q_report.get("breakdown", {}).get("completeness", 0), 1),
        "missing_percentage": round(100 - q_report.get("breakdown", {}).get("completeness", 0), 1),
        "duplicate_percentage": round(100 - q_report.get("breakdown", {}).get("uniqueness", 0), 1),
        "schema_confidence": round(q_report.get("breakdown", {}).get("type_consistency", 0), 1),
        "semantic_confidence": sem_conf,
        "overall_reliability": round(overall, 1)
    }
    
    return {"available_kpis": kpi_data, "omitted_kpis": [], "pipeline_health": pipeline_health}

@router.get("/forecast")
async def get_forecast(metric: str = None, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded")
        
    if metric:
        col_map = {c.lower(): c for c in df.columns}
        if metric.lower() not in col_map:
            return {"available": False, "reason": "Invalid metric column"}
        metric = col_map[metric.lower()]
    
    if not metric:
        semantic_dict = dataset_info.get("semantic_dict")
        if semantic_dict:
            metric = semantic_dict.get("business_terminology", {}).get("primary_metric")
        if not metric:
            from app.services.stats_service import find_column
            metric = find_column(df, r'revenue|sales|amount|\bmrr\b|\barr\b|turnover|income|earnings|\bgmv\b|sales_amount|order_value|net_revenue|total_revenue', numeric_only=True)
            if not metric:
                num_cols = df.select_dtypes(include=[np.number]).columns
                if len(num_cols) > 0:
                    metric = num_cols[0]
                else:
                    return {"available": False, "reason": "No numeric metric column found"}
            
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
        import traceback
        traceback.print_exc()
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
    
    res = []
    import scipy.stats as stats
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    valid_cols = []
    for c in numeric_cols:
        if 'id' in c.lower() and df[c].nunique() == len(df):
            continue
        clean = df[c].dropna()
        if len(clean) == 0:
            continue
        valid_cols.append(c)
    
    # ── Pre-compute cross-column stats needed for importance ──
    total_variance = 0.0
    col_variances = {}
    col_clean = {}
    for c in valid_cols:
        clean = df[c].dropna()
        col_clean[c] = clean
        try:
            v = float(clean.var())
            if np.isfinite(v):
                col_variances[c] = v
                total_variance += v
        except:
            col_variances[c] = 0.0
    
    # Cross-correlation matrix for importance scoring
    if len(valid_cols) >= 2:
        try:
            corr_matrix = df[valid_cols].corr(method='spearman').abs()
        except:
            corr_matrix = None
    else:
        corr_matrix = None

    for col in valid_cols:
        clean_col = col_clean[col]
        n = len(clean_col)
        total_rows = len(df)
        
        coverage = round((n / total_rows) * 100, 1)
        tags = []
        if date_col:
            tags.append("Time Series")
        if coverage == 100:
            tags.append("Healthy")

        # ════════════════════════════════════════════════════════
        # TYPE — Data-driven detection (no name guessing)
        # ════════════════════════════════════════════════════════
        unique_ratio = clean_col.nunique() / n if n > 0 else 0
        is_integer = (clean_col == clean_col.astype(int)).all() if n > 0 else False
        val_min = float(clean_col.min())
        val_max = float(clean_col.max())
        val_mean = float(clean_col.mean())
        val_std = float(clean_col.std()) if n > 1 else 0.0
        
        if is_integer and unique_ratio < 0.02 and clean_col.nunique() <= 10:
            # Very few unique integer values → Categorical/Flag
            metric_type = "Categorical"
        elif is_integer and val_min >= 0 and unique_ratio < 0.15 and clean_col.nunique() <= 50:
            # Low cardinality non-negative integers → Count/Discrete
            metric_type = "Count"
            tags.append("Volume")
        elif 0 <= val_min and val_max <= 1 and val_mean < 1:
            # Values between 0-1 → Ratio/Rate
            metric_type = "Ratio"
        elif 0 <= val_min and val_max <= 100 and is_integer and val_mean > 1:
            # 0-100 integers → could be percentage or score
            if val_std < 30:
                metric_type = "Score"
            else:
                metric_type = "Percentage"
        elif val_std > val_mean * 2 and val_max > 10000:
            # High variance + large values → Financial/Monetary
            metric_type = "Financial"
            tags.append("Financial")
        elif val_min >= 0 and val_max > 100 and val_std > val_mean * 0.5:
            # Large spread, positive values → Revenue/Amount type
            metric_type = "Financial"
            tags.append("Financial")
        elif val_min < 0:
            # Contains negatives → could be margin, change, delta
            metric_type = "Delta"
        else:
            # General continuous numeric
            metric_type = "Continuous"
        
        # ════════════════════════════════════════════════════════
        # IMPORTANCE — Multi-factor statistical scoring (0-100)
        # ════════════════════════════════════════════════════════
        importance_score = 0.0
        
        # Factor 1: Variance Contribution (0-25 pts)
        # How much of total dataset variance does this column explain?
        if total_variance > 0 and col in col_variances:
            var_share = col_variances[col] / total_variance
            importance_score += min(25, var_share * 100)
        
        # Factor 2: Cross-Correlation Strength (0-25 pts)
        # Columns correlated with many others are more "central"
        if corr_matrix is not None and col in corr_matrix.columns:
            other_corrs = corr_matrix[col].drop(col, errors='ignore')
            if len(other_corrs) > 0:
                avg_corr = float(other_corrs.mean())
                max_corr = float(other_corrs.max())
                # High avg correlation = hub metric
                importance_score += avg_corr * 15 + (max_corr * 10 if max_corr > 0.5 else 0)
        
        # Factor 3: Information Entropy (0-25 pts)
        # Higher entropy = more informative column
        try:
            value_counts = clean_col.value_counts(normalize=True)
            entropy = float(stats.entropy(value_counts))
            max_entropy = np.log(min(n, clean_col.nunique())) if clean_col.nunique() > 1 else 1
            norm_entropy = entropy / max_entropy if max_entropy > 0 else 0
            importance_score += norm_entropy * 25
        except:
            importance_score += 12  # neutral fallback

        # Factor 4: Temporal Signal Strength (0-25 pts)
        # If time-series exists, how strong is the temporal pattern?
        if date_col and n > 10:
            try:
                df_temp = df[[date_col, col]].copy()
                df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
                df_temp = df_temp.dropna()
                if len(df_temp) > 10:
                    monthly = df_temp.groupby(df_temp[date_col].dt.to_period('M'))[col].sum()
                    if len(monthly) >= 3:
                        y = monthly.values.astype(float)
                        x = np.arange(len(y))
                        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                        r2 = r_value ** 2
                        # Strong temporal pattern = high importance
                        importance_score += r2 * 20
                        # Significant trend adds bonus
                        if p_value < 0.05:
                            importance_score += 5
            except:
                pass
        
        importance = min(100, max(10, round(importance_score)))
        
        if importance > 80:
            tags.append("High Importance")
            tags.append("Primary KPI")

        # ════════════════════════════════════════════════════════
        # CONFIDENCE — Statistical reliability score (0-100)
        # ════════════════════════════════════════════════════════
        confidence_score = 0.0
        
        # Factor 1: Sample Adequacy (0-30 pts)
        # Based on statistical power — how many observations do we have?
        if n >= 1000:
            sample_score = 30
        elif n >= 500:
            sample_score = 25
        elif n >= 100:
            sample_score = 20
        elif n >= 30:
            sample_score = 15  # Minimum for CLT
        elif n >= 10:
            sample_score = 8
        else:
            sample_score = 3
        confidence_score += sample_score
        
        # Factor 2: Distribution Stability (0-25 pts)
        # Split data in half, compare distributions — stable = high confidence
        if n >= 20:
            try:
                half = n // 2
                first_half = clean_col.iloc[:half]
                second_half = clean_col.iloc[half:]
                ks_stat, ks_p = stats.ks_2samp(first_half, second_half)
                # p > 0.05 means distributions are similar (stable)
                if ks_p > 0.1:
                    confidence_score += 25  # Very stable
                elif ks_p > 0.05:
                    confidence_score += 20
                elif ks_p > 0.01:
                    confidence_score += 12
                else:
                    confidence_score += 5  # Distributions differ significantly
            except:
                confidence_score += 12
        
        # Factor 3: Outlier Ratio Impact (0-20 pts) — shape-aware (skew-robust) detection
        outlier_count = 0
        if n > 10:
            try:
                outlier_count = robust_outlier_stats(clean_col)["count"]
                outlier_ratio = outlier_count / n
                if outlier_ratio == 0:
                    confidence_score += 20
                elif outlier_ratio < 0.01:
                    confidence_score += 16
                elif outlier_ratio < 0.05:
                    confidence_score += 10
                else:
                    confidence_score += 3
                if outlier_count > 0:
                    tags.append("Has Outliers")
            except:
                confidence_score += 10
        
        # Factor 4: Coverage completeness (0-15 pts)
        confidence_score += (coverage / 100) * 15
        
        # Factor 5: Coefficient of Variation stability (0-10 pts)
        if val_mean != 0 and n > 1:
            cv = abs(val_std / val_mean)
            if cv < 0.5:
                confidence_score += 10  # Low relative variation
            elif cv < 1.0:
                confidence_score += 7
            elif cv < 2.0:
                confidence_score += 4
            else:
                confidence_score += 1
        
        confidence = min(100, max(5, round(confidence_score)))
        if confidence > 80:
            tags.append("High Confidence")

        # ════════════════════════════════════════════════════════
        # AGGREGATION — Data-driven detection (no guessing)
        # ════════════════════════════════════════════════════════
        # Principle: Additive quantities → SUM, rates/scores → MEAN
        #   - If values are large, high-variance, and grow with row count → SUM
        #   - If values are bounded, low-variance, rate-like → MEAN
        if metric_type in ("Ratio", "Percentage", "Score"):
            aggregation = "MEAN"
        elif metric_type == "Categorical":
            aggregation = "COUNT"
        elif metric_type == "Count":
            aggregation = "SUM"
        elif metric_type == "Financial":
            aggregation = "SUM"
        elif metric_type == "Delta":
            aggregation = "SUM"
        else:
            # Analyze: if grouping by time changes meaning, it's SUM
            # Check if values are "per-record" amounts (SUM) or measurements (MEAN)
            if date_col and n > 20:
                try:
                    df_temp2 = df[[date_col, col]].copy()
                    df_temp2[date_col] = pd.to_datetime(df_temp2[date_col], errors='coerce')
                    df_temp2 = df_temp2.dropna()
                    monthly_sum = df_temp2.groupby(df_temp2[date_col].dt.to_period('M'))[col].sum()
                    monthly_mean = df_temp2.groupby(df_temp2[date_col].dt.to_period('M'))[col].mean()
                    monthly_count = df_temp2.groupby(df_temp2[date_col].dt.to_period('M'))[col].count()
                    
                    # If sum correlates strongly with count, values are additive → SUM
                    if len(monthly_sum) >= 3:
                        corr_sum_count, _ = stats.pearsonr(monthly_sum.values.astype(float), monthly_count.values.astype(float))
                        corr_mean_count, _ = stats.pearsonr(monthly_mean.values.astype(float), monthly_count.values.astype(float))
                        if abs(corr_sum_count) > abs(corr_mean_count) + 0.2:
                            aggregation = "SUM"
                        else:
                            aggregation = "MEAN"
                    else:
                        aggregation = "MEAN"
                except:
                    aggregation = "MEAN"
            else:
                # No time column: check if values look like individual amounts
                if val_min >= 0 and val_max > 100 and val_std > val_mean * 0.3:
                    aggregation = "SUM"
                else:
                    aggregation = "MEAN"
        
        # ════════════════════════════════════════════════════════
        # TREND — already real (kept as-is)
        # ════════════════════════════════════════════════════════
        trend_status = "Flat"
        if date_col and n > 10:
            try:
                df_temp = df[[date_col, col]].copy()
                df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
                df_temp = df_temp.dropna()
                if len(df_temp) > 0:
                    agg_fn = 'sum' if aggregation == 'SUM' else 'mean'
                    monthly = df_temp.groupby(df_temp[date_col].dt.to_period('M'))[col].agg(agg_fn)
                    monthly = monthly.sort_index()
                    if len(monthly) >= 2:
                        y_vals = monthly.values.astype(float)
                        x_vals = np.arange(len(y_vals))
                        slope, _, r_value, _, _ = stats.linregress(x_vals, y_vals)
                        r2 = r_value ** 2
                        
                        last_val = float(y_vals[-1])
                        prev_val = float(y_vals[-2])
                        recent_delta = last_val - prev_val
                        mean_val = np.mean(y_vals)
                        norm_slope = slope / mean_val if mean_val != 0 else slope
                        
                        if abs(norm_slope) < 0.01 and r2 < 0.3:
                            trend_status = "Stable"
                        elif r2 < 0.3 and ((slope > 0 and recent_delta < 0) or (slope < 0 and recent_delta > 0)):
                            trend_status = "Mixed Trend"
                        elif slope > 0:
                            if r2 >= 0.7: trend_status = "Strong Growing"
                            elif r2 <= 0.4: trend_status = "Weak Growing"
                            else: trend_status = "Growing"
                        elif slope < 0:
                            if r2 >= 0.7: trend_status = "Strong Declining"
                            elif r2 <= 0.4: trend_status = "Weak Declining"
                            else: trend_status = "Declining"
                        else:
                            trend_status = "Stable"
            except:
                pass

        # ════════════════════════════════════════════════════════
        # HEALTH — already real (kept as-is + enhanced)
        # ════════════════════════════════════════════════════════
        missing_pct = 100 - coverage
        outliers_pct = 0.0
        if outlier_count > 0:
            outliers_pct = (outlier_count / n) * 100
            
        full_row_dups = df.duplicated().sum()
        dup_pct = (int(full_row_dups) / len(df)) * 100 if len(df) else 0

        health = max(0, round(100 - missing_pct - (outliers_pct * 0.5) - (dup_pct * 0.25), 1))
        
        if (clean_col < 0).any() and metric_type not in ("Delta",):
            tags.append("Needs Attention")
        
        if date_col and n > 20:
            tags.append("Forecast Ready")

        res.append({
            "name": col,
            "type": metric_type,
            "importance": importance,
            "health": health,
            "coverage": coverage,
            "trend": trend_status,
            "confidence": confidence,
            "aggregation": aggregation,
            "tags": tags
        })
    
    # Sort by importance descending
    res.sort(key=lambda x: x["importance"], reverse=True)
    return res

@router.get("/metrics/{metric}/intelligence")
async def get_metric_intelligence(metric: str, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataframe not found")
        
    if metric not in df.columns or not pd.api.types.is_numeric_dtype(df[metric]):
        raise HTTPException(status_code=400, detail="Invalid or non-numeric metric")

    from app.services.stats_service import find_column
    import scipy.stats as stats
    date_col = find_column(df, r'date|month|year|time')
    
    col_data = df[metric]
    clean_col = col_data.dropna()
    
    total_rows = len(df)
    valid_rows = len(clean_col)
    missing_rows = total_rows - valid_rows
    coverage = round((valid_rows / total_rows) * 100, 2) if total_rows else 0
    
    # ── Deep statistical analysis (no name-pattern guessing) ──
    import scipy.stats as stats_module

    n = len(clean_col)
    val_min  = float(clean_col.min())
    val_max  = float(clean_col.max())
    val_mean = float(clean_col.mean())
    val_std  = float(clean_col.std()) if n > 1 else 0.0
    unique_ratio = clean_col.nunique() / n if n > 0 else 0

    try:
        is_integer_col = bool((clean_col == clean_col.astype(int)).all())
    except Exception:
        is_integer_col = False

    # ── TYPE (data-driven, not name-guessing) ──
    if is_integer_col and unique_ratio < 0.02 and clean_col.nunique() <= 10:
        metric_type = "Categorical"
    elif is_integer_col and val_min >= 0 and unique_ratio < 0.15 and clean_col.nunique() <= 50:
        metric_type = "Count"
    elif 0 <= val_min and val_max <= 1 and val_mean < 1:
        metric_type = "Ratio"
    elif 0 <= val_min and val_max <= 100 and is_integer_col and val_mean > 1:
        metric_type = "Score" if val_std < 30 else "Percentage"
    elif val_std > val_mean * 2 and val_max > 10000:
        metric_type = "Financial"
    elif val_min >= 0 and val_max > 100 and val_std > val_mean * 0.5:
        metric_type = "Financial"
    elif val_min < 0:
        metric_type = "Delta"
    else:
        metric_type = "Continuous"

    # ── AGGREGATION (correlation-based, not name-guessing) ──
    if metric_type in ("Ratio", "Percentage", "Score"):
        aggregation = "MEAN"
    elif metric_type == "Categorical":
        aggregation = "COUNT"
    elif metric_type in ("Count", "Financial", "Delta"):
        aggregation = "SUM"
    else:
        # Continuous: check if monthly sum correlates more with row count than monthly mean does
        if date_col and n > 20:
            try:
                df_tmp2 = df[[date_col, metric]].copy()
                df_tmp2[date_col] = pd.to_datetime(df_tmp2[date_col], errors='coerce')
                df_tmp2 = df_tmp2.dropna()
                mthly_sum   = df_tmp2.groupby(df_tmp2[date_col].dt.to_period('M'))[metric].sum()
                mthly_mean  = df_tmp2.groupby(df_tmp2[date_col].dt.to_period('M'))[metric].mean()
                mthly_count = df_tmp2.groupby(df_tmp2[date_col].dt.to_period('M'))[metric].count()
                if len(mthly_sum) >= 3:
                    cs, _ = stats_module.pearsonr(mthly_sum.values.astype(float), mthly_count.values.astype(float))
                    cm, _ = stats_module.pearsonr(mthly_mean.values.astype(float), mthly_count.values.astype(float))
                    aggregation = "SUM" if abs(cs) > abs(cm) + 0.2 else "MEAN"
                else:
                    aggregation = "MEAN"
            except Exception:
                aggregation = "MEAN"
        else:
            aggregation = "SUM" if (val_min >= 0 and val_max > 100 and val_std > val_mean * 0.3) else "MEAN"

    current_val = float(clean_col.sum()) if aggregation == "SUM" else float(clean_col.mean())

    # ── IMPORTANCE — 4-factor statistical scoring (0-100) ──
    importance_score = 0.0

    # Factor 1: Variance Contribution vs. all numeric columns (0-25 pts)
    numeric_cols_all = df.select_dtypes(include=[np.number]).columns
    try:
        total_var = sum(
            float(df[c].dropna().var())
            for c in numeric_cols_all
            if np.isfinite(df[c].dropna().var()) and df[c].dropna().var() > 0
        )
        my_var = float(clean_col.var())
        if total_var > 0 and np.isfinite(my_var):
            importance_score += min(25, (my_var / total_var) * 100)
    except Exception:
        pass

    # Factor 2: Cross-correlation centrality (0-25 pts)
    if len(numeric_cols_all) >= 2:
        try:
            corr_mat = df[numeric_cols_all].corr(method='spearman').abs()
            if metric in corr_mat.columns:
                others = corr_mat[metric].drop(metric, errors='ignore').dropna()
                if len(others) > 0:
                    avg_corr = float(others.mean())
                    max_corr = float(others.max())
                    importance_score += avg_corr * 15 + (max_corr * 10 if max_corr > 0.5 else 0)
        except Exception:
            pass

    # Factor 3: Information entropy (0-25 pts)
    try:
        vc = clean_col.value_counts(normalize=True)
        entropy_val = float(stats_module.entropy(vc))
        max_ent = np.log(min(n, clean_col.nunique())) if clean_col.nunique() > 1 else 1
        norm_ent = entropy_val / max_ent if max_ent > 0 else 0
        importance_score += norm_ent * 25
    except Exception:
        importance_score += 12

    # Factor 4: Temporal signal strength (0-25 pts)
    if date_col and n > 10:
        try:
            df_t = df[[date_col, metric]].copy()
            df_t[date_col] = pd.to_datetime(df_t[date_col], errors='coerce')
            df_t = df_t.dropna()
            if len(df_t) > 10:
                mthly = df_t.groupby(df_t[date_col].dt.to_period('M'))[metric].sum()
                if len(mthly) >= 3:
                    y_t = mthly.values.astype(float)
                    x_t = np.arange(len(y_t))
                    sl, inter, rv, pv, se = stats_module.linregress(x_t, y_t)
                    r2_temp = rv ** 2
                    importance_score += r2_temp * 20
                    if pv < 0.05:
                        importance_score += 5
        except Exception:
            pass

    importance = min(100, max(10, round(importance_score)))

    # ── CONFIDENCE — 5-factor statistical reliability (0-100) ──
    confidence_score = 0.0

    # Factor 1: Sample adequacy (0-30 pts)
    if   n >= 1000: confidence_score += 30
    elif n >=  500: confidence_score += 25
    elif n >=  100: confidence_score += 20
    elif n >=   30: confidence_score += 15
    elif n >=   10: confidence_score += 8
    else:           confidence_score += 3

    # Factor 2: Distribution stability – KS test on two halves (0-25 pts)
    if n >= 20:
        try:
            half = n // 2
            ks_stat, ks_p = stats_module.ks_2samp(clean_col.iloc[:half], clean_col.iloc[half:])
            if   ks_p > 0.1:  confidence_score += 25
            elif ks_p > 0.05: confidence_score += 20
            elif ks_p > 0.01: confidence_score += 12
            else:              confidence_score += 5
        except Exception:
            confidence_score += 12

    # Factor 3: Outlier ratio (0-20 pts) — shape-aware (skew-robust) detection
    outlier_count_intel = 0
    if n > 10:
        try:
            outlier_count_intel = robust_outlier_stats(clean_col)["count"]
            outlier_ratio = outlier_count_intel / n
            if   outlier_ratio == 0:    confidence_score += 20
            elif outlier_ratio < 0.01:  confidence_score += 16
            elif outlier_ratio < 0.05:  confidence_score += 10
            else:                       confidence_score += 3
        except Exception:
            confidence_score += 10

    # Factor 4: Coverage completeness (0-15 pts)
    confidence_score += (coverage / 100) * 15

    # Factor 5: Coefficient of Variation stability (0-10 pts)
    if val_mean != 0 and n > 1:
        cv_val = abs(val_std / val_mean)
        if   cv_val < 0.5: confidence_score += 10
        elif cv_val < 1.0: confidence_score += 7
        elif cv_val < 2.0: confidence_score += 4
        else:              confidence_score += 1

    confidence = min(100, max(5, round(confidence_score)))

    # ── BUILD TAGS ──
    intel_tags = []
    if date_col:
        intel_tags.append("Time Series")
    if coverage == 100:
        intel_tags.append("Healthy")
    if importance > 80:
        intel_tags.extend(["High Importance", "Primary KPI"])
    if confidence > 80:
        intel_tags.append("High Confidence")
    if outlier_count_intel > 0:
        intel_tags.append("Has Outliers")
    if date_col and n > 20:
        intel_tags.append("Forecast Ready")
    if metric_type == "Financial":
        intel_tags.append("Financial")
    if metric_type == "Count":
        intel_tags.append("Volume")

    missing_pct = 100 - coverage
    full_row_dups = df.duplicated().sum()
    dup_pct = (int(full_row_dups) / total_rows) * 100 if total_rows else 0
    unique_pct = 100 - dup_pct

    outliers_pct = 0.0
    if len(clean_col) > 10:
        try:
            outliers_count = robust_outlier_stats(clean_col)["count"]
            outliers_pct = (outliers_count / valid_rows) * 100
        except:
            pass

    health_score = max(0, round(100 - missing_pct - (outliers_pct * 0.5) - (dup_pct * 0.25), 1))

    overview = {
        "name": metric,
        "description": f"Deep statistical analysis of '{metric}' — type detected from value distribution, not column name.",
        "category": metric_type,
        "currentValue": current_val,
        "aggregation": aggregation,
        "coverage": coverage,
        "health": health_score,
        "importance": importance,
        "confidence": confidence,
        "tags": intel_tags,
        "healthBreakdown": {
            "formula": "100 - missing% - (outlier% * 0.5) - (duplicate% * 0.25)",
            "missingPenalty": f"-{round(missing_pct, 1)} pts",
            "outlierPenalty": f"-{round(outliers_pct * 0.5, 1)} pts",
            "duplicatePenalty": f"-{round(dup_pct * 0.25, 1)} pts"
        },
        "importanceBreakdown": {
            "varianceContribution": "0-25 pts: share of total dataset variance",
            "crossCorrelation": "0-25 pts: Spearman centrality across all numeric cols",
            "informationEntropy": "0-25 pts: Shannon entropy normalized by max entropy",
            "temporalSignal": "0-25 pts: R² of linear trend on monthly aggregates"
        },
        "confidenceBreakdown": {
            "sampleAdequacy": "0-30 pts: statistical power from row count",
            "distributionStability": "0-25 pts: KS-test on first vs second half",
            "outlierRatio": "0-20 pts: Z-score |z|>3 outlier penalty",
            "coverageCompleteness": "0-15 pts: non-null fraction",
            "cvStability": "0-10 pts: coefficient of variation stability"
        }
    }
    
    q1 = float(clean_col.quantile(0.25))
    q3 = float(clean_col.quantile(0.75))
    iqr = q3 - q1
    
    stats_data = {
        "count": valid_rows,
        "sum": float(clean_col.sum()),
        "mean": float(clean_col.mean()),
        "median": float(clean_col.median()),
        "mode": float(clean_col.mode().iloc[0]) if not clean_col.mode().empty else None,
        "min": float(clean_col.min()),
        "max": float(clean_col.max()),
        "variance": float(clean_col.var()),
        "std_dev": float(clean_col.std()),
        "cv": float(clean_col.std() / clean_col.mean()) if clean_col.mean() != 0 else 0,
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "p95": float(clean_col.quantile(0.95)),
        "p99": float(clean_col.quantile(0.99))
    }
    
    try:
        skewness = float(stats.skew(clean_col))
        kurtosis = float(stats.kurtosis(clean_col))
    except:
        skewness = 0.0
        kurtosis = 0.0
        
    counts, bin_edges = np.histogram(clean_col, bins=15)
    histogram = [{"bin": f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}", "count": int(counts[i])} for i in range(len(counts))]
    
    dist_type = "Normal"
    if skewness > 1: dist_type = "Highly Positively Skewed"
    elif skewness < -1: dist_type = "Highly Negatively Skewed"
    elif skewness > 0.5: dist_type = "Moderately Positively Skewed"
    elif skewness < -0.5: dist_type = "Moderately Negatively Skewed"
        
    distribution = {
        "histogram": histogram,
        "skewness": round(skewness, 2),
        "kurtosis": round(kurtosis, 2),
        "type": dist_type
    }
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    correlations = []
    if len(numeric_cols) > 1:
        corr_matrix = df[numeric_cols].corr()
        if metric in corr_matrix:
            metric_corr = corr_matrix[metric].drop(metric)
            metric_corr = metric_corr.dropna().sort_values(key=abs, ascending=False).head(5)
            for m, val in metric_corr.items():
                strength = "Strong" if abs(val) > 0.7 else "Moderate" if abs(val) > 0.3 else "Weak"
                correlations.append({
                    "metric": m,
                    "coefficient": float(val),
                    "type": "Positive" if val > 0 else "Negative",
                    "strength": strength
                })
                
    trend_data = []
    forecast_data = []
    forecast_accuracy = None
    r2 = 0.0
    slope = 0.0
    peak = None
    recovery = None
    decline = None

    if date_col:
        df_temp = df.copy()
        df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
        df_temp = df_temp.dropna(subset=[date_col])
        if len(df_temp) > 0:
            monthly = df_temp.groupby(df_temp[date_col].dt.to_period('M'))[metric].agg('sum' if aggregation == 'SUM' else 'mean').reset_index()
            monthly = monthly.sort_values(date_col)

            y = monthly[metric].values
            x = np.arange(len(y))
            if len(y) > 2:
                try:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                    r2 = r_value ** 2
                except Exception:
                    pass

            # Forecast projection reuses the same seasonality-aware, backtested
            # engine as /analytics/forecast instead of a second ad-hoc linregress
            # fit, so both endpoints agree on methodology and CI handling.
            fc_result = forecast_series(df_temp, metric, periods=3, agg='mean' if aggregation != 'SUM' else 'sum')
            if fc_result.get("available"):
                forecast_data = [
                    {"period": f["date"], "forecast": f["forecast"]}
                    for f in fc_result.get("forecast", [])
                ]
                forecast_accuracy = fc_result.get("accuracy")

            for i, row in monthly.iterrows():
                val = float(row[metric])
                name = row[date_col].strftime('%b %Y')
                trend_data.append({
                    "period": name,
                    "value": val
                })
                if peak is None or val > peak["value"]:
                    peak = {"period": name, "value": val}
            
            max_inc = -float('inf')
            max_dec = float('inf')
            for i in range(1, len(trend_data)):
                diff = trend_data[i]["value"] - trend_data[i-1]["value"]
                if diff > max_inc:
                    max_inc = diff
                    recovery = {"period": trend_data[i]["period"], "diff": diff}
                if diff < max_dec:
                    max_dec = diff
                    decline = {"period": trend_data[i]["period"], "diff": diff}

    # Duplicates, outliers, and health_score are now computed earlier for overview.
    
    badge = "Excellent" if health_score >= 95 else "Good" if health_score >= 75 else "Warning"
    badge = "Excellent" if health_score >= 95 else "Good" if health_score >= 75 else "Warning"

    quality = {
        "missingPct": missing_pct,
        "duplicatePct": dup_pct,
        "uniquePct": unique_pct,
        "outliersPct": outliers_pct,
        "healthScore": health_score,
        "badge": badge
    }
    
    calculation = {
        "formula": f"{aggregation}({metric})",
        "python": f'df["{metric}"].{aggregation.lower()}()',
        "sql": f'SELECT {aggregation}({metric}) FROM dataset;',
        "rowsUsed": valid_rows,
        "missingRemoved": missing_rows,
        "filtersApplied": "None"
    }
    
    relationships = ["Dashboard", "KPI Center"]
    if date_col: relationships.append("Forecast")
    if len(correlations) > 0: relationships.append("Correlation")
        
    trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
    trend_desc = "consistently " if r2 >= 0.4 else "slightly " if r2 > 0 else ""
    dist_note = (
        f"Distribution is positively skewed due to a few high-value transactions." if "positive" in dist_type.lower() else 
        f"Distribution is negatively skewed due to a few lower-bound transactions." if "negative" in dist_type.lower() else 
        f"Distribution is fairly balanced and symmetric."
    )

    return {
        "overview": overview,
        "statistics": stats_data,
        "trend": {
            "data": trend_data,
            "slope": slope,
            "r2": r2,
            "peak": peak,
            "recovery": recovery,
            "decline": decline
        },
        "distribution": distribution,
        "correlation": correlations,
        "forecast": forecast_data,
        "forecastAccuracy": forecast_accuracy,
        "quality": quality,
        "calculation": calculation,
        "relationships": relationships,
        "analystNotes": [
            f"{metric} reached its highest level in {peak['period']}." if peak else f"{metric} has remained relatively consistent without major peaks.",
            f"Overall trend has been {trend_desc}{trend_direction} over the observed period.",
            f"Only {outliers_pct:.1f}% observations were detected as statistical outliers (Coverage: {coverage}%).",
            dist_note
        ]
    }

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

from app.core.database import get_db_connection
from app.core.config import DB_PATH

@router.get("/confidence")
async def get_confidence(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"insights": {"verified": 0, "unverified": 0}, "recommendations": {"verified": 0, "unverified": 0}, "audit_trail": []}
        
    conn = get_db_connection()
    conn.row_factory = None
    cursor = conn.cursor()
    
    # Insights stats
    cursor.execute('SELECT verified, count(*) as count FROM insights WHERE user_id = %s AND dataset_id = %s GROUP BY verified', (current_user["id"], dataset_info["id"]))
    ins_stats = cursor.fetchall()
    ins_verified = 0
    ins_unverified = 0
    for row in ins_stats:
        if row["verified"] == 1: ins_verified = row["count"]
        else: ins_unverified = row["count"]
        
    # Recommendations stats
    cursor.execute('SELECT verified, count(*) as count FROM recommendations WHERE user_id = %s AND dataset_id = %s GROUP BY verified', (current_user["id"], dataset_info["id"]))
    rec_stats = cursor.fetchall()
    rec_verified = 0
    rec_unverified = 0
    for row in rec_stats:
        if row["verified"] == 1: rec_verified = row["count"]
        else: rec_unverified = row["count"]
        
    # Audit trail (recent insights)
    cursor.execute('SELECT id, title, description, audit_sql, confidence, verified FROM insights WHERE user_id = %s AND dataset_id = %s ORDER BY created_at DESC LIMIT 100', (current_user["id"], dataset_info["id"]))
    audit_trail = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    
    return {
        "insights": {"verified": ins_verified, "unverified": ins_unverified},
        "recommendations": {"verified": rec_verified, "unverified": rec_unverified},
        "audit_trail": audit_trail
    }
