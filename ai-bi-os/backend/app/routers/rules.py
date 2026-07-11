import pandas as pd
import numpy as np
import os
import json
import uuid
from datetime import datetime
import sqlite3
import re
from fastapi import APIRouter, Depends, Body
from app.services.data_processing import get_active_dataset, get_dataframe
from app.core.security import get_current_user
from app.core.config import DB_PATH, LLM_MODEL
from litellm import completion

router = APIRouter()

@router.get("/")
async def get_rules(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []
        
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rules WHERE user_id = ? AND dataset_id = ? ORDER BY created_at DESC', (current_user["id"], dataset_info["id"]))
    rules = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    # Evaluate rules deterministically
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is not None:
        from app.services.stats_service import find_column
        date_col = find_column(df, r'date|month|year|time')
        
        for rule in rules:
            rule["status"] = "OK"
            rule["current_value"] = None
            if not rule["is_active"]:
                rule["status"] = "INACTIVE"
                continue
                
            metric = rule["metric_column"]
            if metric not in df.columns or not pd.api.types.is_numeric_dtype(df[metric]):
                rule["status"] = "ERROR (Invalid Metric)"
                continue
                
            df_temp = df.copy()
            if date_col and rule["window"] == "MoM":
                df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
                df_temp = df_temp.dropna(subset=[date_col])
                if not df_temp.empty:
                    monthly = df_temp.groupby(df_temp[date_col].dt.to_period('M'))[metric].sum()
                    if len(monthly) >= 2:
                        sorted_periods = sorted(monthly.index)
                        recent = float(monthly[sorted_periods[-1]])
                        prior = float(monthly[sorted_periods[-2]])
                        rule["current_value"] = recent
                        
                        if prior > 0:
                            pct_change = ((recent - prior) / prior) * 100
                            rule["current_value"] = pct_change
                            
                            cond = rule["condition"]
                            thresh = rule["threshold"]
                            
                            if cond == ">" and pct_change > thresh: rule["status"] = "TRIGGERED"
                            elif cond == "<" and pct_change < thresh: rule["status"] = "TRIGGERED"
                            elif cond == ">=" and pct_change >= thresh: rule["status"] = "TRIGGERED"
                            elif cond == "<=" and pct_change <= thresh: rule["status"] = "TRIGGERED"
            else:
                # Latest value
                val = float(df_temp[metric].sum())
                rule["current_value"] = val
                cond = rule["condition"]
                thresh = rule["threshold"]
                if cond == ">" and val > thresh: rule["status"] = "TRIGGERED"
                elif cond == "<" and val < thresh: rule["status"] = "TRIGGERED"
                elif cond == ">=" and val >= thresh: rule["status"] = "TRIGGERED"
                elif cond == "<=" and val <= thresh: rule["status"] = "TRIGGERED"
                
    return rules

@router.post("/")
async def create_rule(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"error": "No dataset"}
        
    rule_id = f"rule_{uuid.uuid4().hex[:8]}"
    created_at = datetime.utcnow().isoformat()
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO rules (id, user_id, dataset_id, name, metric_column, condition, threshold, window, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        rule_id, current_user["id"], dataset_info["id"],
        data.get("name", "New Rule"),
        data.get("metric_column", ""),
        data.get("condition", ">"),
        float(data.get("threshold", 0)),
        data.get("window", "latest"),
        1, created_at
    ))
    conn.commit()
    conn.close()
    return {"id": rule_id, "success": True}

@router.delete("/{rule_id}")
async def delete_rule(rule_id: str, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('DELETE FROM rules WHERE id = ? AND user_id = ?', (rule_id, current_user["id"]))
    conn.commit()
    conn.close()
    return {"success": True}

@router.post("/parse-text")
async def parse_text_rule(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    text = data.get("text", "")
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"error": "No dataset"}
        
    df = get_dataframe(dataset_info["id"], current_user["id"])
    cols = df.columns.tolist() if df is not None else []
    
    prompt = f"""Given the following dataset columns: {cols}
Parse the user's natural language business rule into a JSON object.
Rule text: "{text}"
Return a valid JSON object with:
- name (string, a short title for the rule)
- metric_column (string, MUST be exactly one of the available columns)
- condition (string, one of: ">", "<", ">=", "<=", "==")
- threshold (number)
- window (string, either "MoM" or "latest")"""

    try:
        res = completion(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            api_key=os.getenv("GROQ_API_KEY")
        )
        content = res.choices[0].message.content
        m = re.search(r'\{.*\}', content, re.DOTALL)
        if m:
            content = m.group(0)
        parsed = json.loads(content)
        return {"success": True, "parsed": parsed}
    except Exception as e:
        return {"success": False, "error": str(e)}
