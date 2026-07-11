import pandas as pd
import numpy as np
import re
import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends
from app.services.data_processing import get_active_dataset, get_dataframe
from app.core.security import get_current_user
from app.services.query.duckdb_engine import DuckDBEngine
from app.services.data_processing import get_dataset_path
from app.services.insights_engine import DeepInsightsEngine
import sqlite3
from litellm import completion
from app.core.config import DB_PATH, LLM_MODEL

router = APIRouter()

def find_column(df: pd.DataFrame, pattern: str) -> str:
    for col in df.columns:
        if re.search(pattern, col, re.IGNORECASE):
            return col
    return None

@router.get("/executive-summary")
async def get_executive_summary(current_user: dict = Depends(get_current_user)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        return {"summary": "AI features are not configured - add GROQ_API_KEY to your .env file.", "verified": False}
        
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"summary": "No dataset uploaded yet. Upload a dataset to see AI insights.", "verified": False}
        
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        return {"summary": "Failed to load data.", "verified": False}

    # Compute deterministic facts
    row_count = len(df)
    
    rev_col = find_column(df, r'revenue|sales|amount|mrr|arr|turnover|income|earnings|gmv|sales_amount|order_value|net_revenue|total_revenue')
    date_col = find_column(df, r'date|month|year|time')
    
    facts = {
        "dataset_name": dataset_info["name"],
        "row_count": row_count
    }
    
    if rev_col and pd.api.types.is_numeric_dtype(df[rev_col]):
        total_value = float(df[rev_col].sum())
        facts["total_value"] = total_value
        facts["metric_name"] = rev_col
        
        if date_col:
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                df_clean = df.dropna(subset=[date_col])
                if not df_clean.empty:
                    periods = df_clean.groupby(df_clean[date_col].dt.to_period('M'))
                    if len(periods) >= 2:
                        sorted_periods = sorted(periods.groups.keys())
                        recent = float(periods.get_group(sorted_periods[-1])[rev_col].sum())
                        prior = float(periods.get_group(sorted_periods[-2])[rev_col].sum())
                        if prior > 0:
                            pct_change = ((recent - prior) / prior) * 100
                            facts["percent_change"] = round(pct_change, 1)
            except Exception:
                pass
                
    # Prepare LLM Prompt
    prompt = f"Write a 2-3 sentence executive summary based on the following facts. DO NOT invent any numbers. Facts: {facts}"
    
    try:
        response = completion(
            model=LLM_MODEL, 
            messages=[{"role": "user", "content": prompt}],
            api_key=os.getenv("GROQ_API_KEY")
        )
        llm_summary = response.choices[0].message.content.strip()
        
        # Verify numbers
        import string
        def extract_numbers(text):
            return re.findall(r'-?\d+\.?\d*', text.replace(',', ''))
            
        llm_nums = extract_numbers(llm_summary)
        fact_str = str(facts)
        fact_nums = extract_numbers(fact_str)
        
        verified = True
        for num in llm_nums:
            # allow some flexibility for rounding
            found = False
            try:
                num_float = float(num)
                for f_num in fact_nums:
                    if abs(float(f_num) - num_float) < 1.0: # Close enough
                        found = True
                        break
            except Exception:
                pass
            if not found:
                verified = False
                break
                
        if verified:
            return {"summary": llm_summary, "verified": True, "facts": facts}
        else:
            raise Exception("Hallucination detected")
            
    except Exception as e:
        # Fallback to template
        dataset_name = dataset_info['name']
        
        if "total_value" in facts and "metric_name" in facts:
            metric_name = facts['metric_name']
            formatted_total = f"${facts['total_value']:,.2f}"
            
            if "percent_change" in facts:
                pct = facts["percent_change"]
                direction = "increase" if pct > 0 else "decrease"
                summary = f"The {dataset_name} dataset shows total {metric_name} of {formatted_total} across {row_count} records, a {abs(pct):.1f}% {direction} versus the prior period."
            else:
                summary = f"The {dataset_name} dataset shows total {metric_name} of {formatted_total} across {row_count} records."
        else:
            summary = f"The {dataset_name} dataset contains {row_count} records."
            
        return {"summary": summary, "verified": True, "facts": facts}

@router.post("/deep-analyze")
async def deep_analyze(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"success": False, "message": "No active dataset."}
        
    db_engine = DuckDBEngine()
    file_path = get_dataset_path(dataset_info["filepath"])
    format_type = "parquet" if file_path.endswith(".parquet") else "csv"
    db_engine.register_dataset("active_dataset", file_path, format=format_type)
    
    engine = DeepInsightsEngine(db_engine)
    insights = engine.generate_insights(current_user["id"], dataset_info["id"])
    db_engine.close()
    return {"success": True, "insights": insights}

@router.get("/")
async def list_insights(dataset_version_id: str = None, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []
        
    # Check DB first
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM insights 
        WHERE user_id = ? AND dataset_id = ? 
        ORDER BY verified DESC, created_at DESC
    ''', (current_user["id"], dataset_info["id"]))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        return [dict(r) for r in rows]
        
    # Fallback to Z-Score Anomalies
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        return []

    date_col = find_column(df, r'date|month|year|time')
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    anomalies = []

    if date_col and len(numeric_cols) > 0:
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df_clean = df.dropna(subset=[date_col])
            
            # Group by month
            monthly_data = df_clean.groupby(df_clean[date_col].dt.to_period('M'))[numeric_cols].sum()
            
            if len(monthly_data) >= 3: # Need some history
                for col in numeric_cols:
                    series = monthly_data[col]
                    mean = series.mean()
                    std = series.std()
                    
                    if std > 0:
                        recent_val = series.iloc[-1]
                        z_score = (recent_val - mean) / std
                        
                        if abs(z_score) > 1.5:
                            is_drop = z_score < 0
                            category = "Risk" if is_drop else "Opportunity"
                            title = f"Significant {'Drop' if is_drop else 'Spike'} in {col}"
                            desc = f"{col} was {recent_val:.2f} in the most recent period, which is {abs(z_score):.1f} standard deviations from the mean."
                            impact = float(abs(recent_val))
                            
                            anomalies.append({
                                "id": f"ins_{uuid.uuid4().hex[:8]}",
                                "title": title,
                                "description": desc,
                                "category": category,
                                "confidence": round(min(0.99, abs(z_score) / 3), 2),
                                "impact": impact,
                                "verified": 1,
                                "created_at": datetime.utcnow().isoformat()
                            })
        except Exception:
            pass

    if anomalies:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        for a in anomalies:
            cursor.execute('''
                INSERT INTO insights (id, user_id, dataset_id, title, description, category, insight_level, confidence, impact, recommendation, verified, audit_sql, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                a["id"],
                current_user["id"],
                dataset_info["id"],
                a["title"],
                a["description"],
                a["category"],
                "Operational",
                a["confidence"],
                a["impact"],
                "Investigate the cause of this recent anomaly.",
                a["verified"],
                "Computed via Pandas Z-Score Z=(X-μ)/σ",
                a["created_at"]
            ))
        conn.commit()
        conn.close()

    return anomalies
