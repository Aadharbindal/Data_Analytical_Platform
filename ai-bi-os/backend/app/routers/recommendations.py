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
from app.core.config import DB_PATH
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
            if re.search(r'revenue|sales|profit|amount', col, re.IGNORECASE):
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
            model=os.getenv("LLM_MODEL", "groq/llama-3.3-70b-versatile"),
            messages=[{"role": "user", "content": prompt}],
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        content = res.choices[0].message.content
        m = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
        if m:
            content = m.group(0)
        recs = json.loads(content)
        
    except Exception:
        recs = []

    # 4. Accuracy Check & Save
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    final_recs = []
    
    fact_str = json.dumps(facts).replace(',', '')
    fact_nums = re.findall(r'\b\d+(?:\.\d+)?\b', fact_str)
    
    for r in recs:
        rec_str = f"{r.get('title', '')} {r.get('rationale', '')}".replace(',', '')
        rec_nums = re.findall(r'\b\d+(?:\.\d+)?\b', rec_str)
        
        verified = True
        for num in rec_nums:
            try:
                num_float = float(num)
                if num_float == 0: continue
                
                found = False
                for f_num in fact_nums:
                    try:
                        if abs(float(f_num) - num_float) < 1.0:
                            found = True
                            break
                    except:
                        pass
                if not found:
                    verified = False
                    break
            except:
                pass
                
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
