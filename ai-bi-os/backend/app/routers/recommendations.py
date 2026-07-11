import pandas as pd
import numpy as np
import os
import json
import uuid
from datetime import datetime
import sqlite3
import re
from fastapi import APIRouter, Depends
from app.services.data_processing import get_active_dataset, get_dataframe
from app.core.security import get_current_user
from app.core.config import DB_PATH, LLM_MODEL
from app.services.validation import verify_numbers_against_facts
from litellm import completion

router = APIRouter()

def get_cached_recommendations(user_id: str, dataset_id: str):
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM recommendations
        WHERE user_id = ? AND dataset_id = ?
        ORDER BY created_at DESC
    ''', (user_id, dataset_id))
    rows = cursor.fetchall()
    conn.close()
    if rows:
        return [dict(r) for r in rows]
    return []

@router.get("/")
async def get_recommendations(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []
    return get_cached_recommendations(current_user["id"], dataset_info["id"])

@router.post("/generate")
async def generate_recommendations(current_user: dict = Depends(get_current_user)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        return {"success": False, "message": "AI features are not configured - add GROQ_API_KEY to your .env file."}
        
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []

    # 1. Check cache
    cached = get_cached_recommendations(current_user["id"], dataset_info["id"])
    if cached:
        return cached

    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        return []

    # 2. Deterministic Facts
    facts = []
    
    cat_cols = df.select_dtypes(exclude=[np.number, 'datetime64']).columns
    num_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(cat_cols) > 0 and len(num_cols) > 0:
        main_cat = cat_cols[0]
        main_num = num_cols[0]
        for col in num_cols:
            if re.search(r'revenue|sales|profit|amount|mrr|arr|turnover|income|earnings|gmv|sales_amount|order_value|net_revenue|total_revenue', col, re.IGNORECASE):
                main_num = col
                break
        for col in cat_cols:
            if df[col].nunique() < 20 and df[col].nunique() > 1:
                main_cat = col
                break
                
        grouped = df.groupby(main_cat)[main_num].sum().reset_index()
        if len(grouped) > 1:
            grouped = grouped.sort_values(main_num, ascending=False)
            top_cat = grouped.iloc[0]
            bot_cat = grouped.iloc[-1]
            facts.append({
                "type": "Performance",
                "finding": f"Top performing {main_cat} is {top_cat[main_cat]} with {main_num} of {top_cat[main_num]}."
            })
            facts.append({
                "type": "Underperformance",
                "finding": f"Lowest performing {main_cat} is {bot_cat[main_cat]} with {main_num} of {bot_cat[main_num]}."
            })

    if not facts:
        facts.append({
            "type": "General",
            "finding": f"Dataset has {len(df)} rows and {len(df.columns)} columns."
        })

    # 3. LLM Translation
    prompt = f"""Given these hard facts computed from the user's data:
{json.dumps(facts)}

Generate 3 actionable business recommendations. 
CRITICAL: You MUST ONLY cite numbers that are explicitly present in the provided facts. Do not invent, estimate, or guess any figures.
Return ONLY a valid JSON array of objects with keys:
- title (string, action-oriented)
- rationale (string, explain why using the facts and EXACT numbers)
- priority (string, High, Medium, Low)
- category (string)"""

    try:
        res = completion(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            api_key=os.getenv("GROQ_API_KEY"),
            max_tokens=2000
        )
        
        content = res.choices[0].message.content
        
        # Try direct JSON parse first
        try:
            clean_content = content
            m = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
            if m:
                clean_content = m.group(1)
            recs = json.loads(clean_content)
        except json.JSONDecodeError as jde:
            # Fallback to regex
            m = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
            if m:
                recs = json.loads(m.group(0))
            else:
                raise ValueError(f"JSON Parse Error: {jde}. Response was: {content}")
        
    except Exception as e:
        import traceback
        import logging
        logging.error(f"[recommendations] LLM call/parse failed: {type(e).__name__}: {e}")
        logging.error(traceback.format_exc())
        return {"success": False, "message": f"Failed to generate recommendations: {str(e)}"}

    # 4. Accuracy Check & Save
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    final_recs = []
    fact_str = json.dumps(facts)
    
    for r in recs:
        rec_str = f"{r.get('title', '')} {r.get('rationale', '')}"
        verified = verify_numbers_against_facts(rec_str, fact_str)
        
        rec_id = f"rec_{uuid.uuid4().hex[:8]}"
        created_at = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO recommendations (id, user_id, dataset_id, title, rationale, priority, category, verified, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rec_id,
            current_user["id"],
            dataset_info["id"],
            r.get("title", "Recommendation"),
            r.get("rationale", ""),
            r.get("priority", "Medium"),
            r.get("category", "General"),
            1 if verified else 0,
            created_at
        ))
        
        r["id"] = rec_id
        r["verified"] = verified
        final_recs.append(r)
        
    conn.commit()
    conn.close()
    
    return final_recs
