import pandas as pd
import numpy as np
import re
import os
from fastapi import APIRouter, Depends
from app.services.data_processing import get_active_dataset, get_dataframe
from app.core.security import get_current_user
from litellm import completion

router = APIRouter()

def find_column(df: pd.DataFrame, pattern: str) -> str:
    for col in df.columns:
        if re.search(pattern, col, re.IGNORECASE):
            return col
    return None

@router.get("/executive-summary")
async def get_executive_summary(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"summary": "No dataset uploaded yet. Upload a dataset to see AI insights.", "verified": False}
        
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        return {"summary": "Failed to load data.", "verified": False}

    # Compute deterministic facts
    row_count = len(df)
    
    rev_col = find_column(df, r'revenue|sales|amount')
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
            model="groq/llama-3.3-70b-versatile", 
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
            return {"summary": llm_summary, "verified": True}
        else:
            raise Exception("Hallucination detected")
            
    except Exception as e:
        # Fallback to template
        summary = f"Based on the recently uploaded dataset '{dataset_info['name']}' which contains {row_count} records."
        if "total_value" in facts:
            summary += f" The total {facts['metric_name']} is {facts['total_value']}."
        if "percent_change" in facts:
            change_dir = "increase" if facts["percent_change"] > 0 else "decrease"
            summary += f" There is a {abs(facts['percent_change'])}% {change_dir} in the recent period."
        return {"summary": summary, "verified": True}

@router.get("/")
async def list_insights(dataset_version_id: str = None, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []
        
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        return []

    date_col = find_column(df, r'date|month|year|time')
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    anomalies = []
    insight_id = 1

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
                            impact = "High" if abs(z_score) > 2.0 else "Medium"
                            
                            anomalies.append({
                                "id": f"insight_{insight_id}",
                                "title": title,
                                "description": desc,
                                "category": category,
                                "confidence": round(min(0.99, abs(z_score) / 3), 2),
                                "impact": impact,
                                "verified": True,
                                "created_at": pd.Timestamp.utcnow().isoformat()
                            })
                            insight_id += 1
        except Exception:
            pass

    return anomalies
