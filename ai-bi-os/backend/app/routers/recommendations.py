import pandas as pd
import numpy as np
import os
import json
import uuid
import logging
from datetime import datetime
from app.core.database import get_db_connection
import re
from fastapi import APIRouter, Depends
from app.services.data_processing import get_active_dataset, get_dataframe
from app.core.security import get_current_user
from app.core.config import DB_PATH, LLM_MODEL
from app.services.validation import verify_numbers_against_facts
from litellm import completion

router = APIRouter()

def get_cached_recommendations(user_id: str, dataset_id: str):
    conn = get_db_connection()
    conn.row_factory = None
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM recommendations
        WHERE user_id = %s AND dataset_id = %s
        ORDER BY created_at DESC
    ''', (user_id, dataset_id))
    rows = cursor.fetchall()
    conn.close()
    if rows:
        return [dict(r) for r in rows]
    return []

@router.get("")
async def list_recommendations(dataset_version_id: str = None, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []
    return get_cached_recommendations(current_user["id"], dataset_info["id"])

@router.post("/generate")
async def generate_recommendations(force: bool = False, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []

    # 1. Check cache (only if force is False)
    if not force:
        cached = get_cached_recommendations(current_user["id"], dataset_info["id"])
        if cached:
            return cached

    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None or len(df) == 0:
        return []

    # 2. Deterministic Facts
    domain = dataset_info.get("domain", "generic")
    semantic_dict = dataset_info.get("semantic_dict", {})
    bus_term = semantic_dict.get("business_terminology", {}) if semantic_dict else {}
    sem_dict = semantic_dict.get("semantic_dictionary", {}) if semantic_dict else {}
    
    main_num = bus_term.get("primary_metric") if bus_term else None
    if not main_num or main_num not in df.columns:
        num_cols = df.select_dtypes(include=[np.number]).columns
        main_num = num_cols[0] if len(num_cols) > 0 else None
        
    main_cat = None
    cat_fields = sem_dict.get("categorical_fields", []) if sem_dict else []
    if cat_fields:
        for col in cat_fields:
            if col in df.columns and df[col].nunique() < 50 and df[col].nunique() > 1:
                main_cat = col
                break
    if not main_cat:
        cat_cols = df.select_dtypes(exclude=[np.number, 'datetime64']).columns
        for col in cat_cols:
            if df[col].nunique() < 50 and df[col].nunique() > 1:
                main_cat = col
                break

    # Calculate metrics
    top_category_share = 0
    top_cat_name = ""
    if main_cat and main_num:
        grouped = df.groupby(main_cat, observed=True)[main_num].sum().reset_index()
        total_sum = grouped[main_num].sum()
        if total_sum > 0:
            top_category = grouped.sort_values(main_num, ascending=False).iloc[0]
            top_category_share = top_category[main_num] / total_sum
            top_cat_name = str(top_category[main_cat])
            
    failure_rate = 0
    status_col = None
    if sem_dict:
        status_fields = sem_dict.get("status_fields", [])
        unhealthy_regex = sem_dict.get("unhealthy_regex", "(?i)(fail|error|decline|reject|timeout)")
        if status_fields:
            for col in status_fields:
                if col in df.columns:
                    status_col = col
                    break
        if status_col and unhealthy_regex:
            total_rows = len(df)
            if total_rows > 0:
                failures = df[status_col].astype(str).str.contains(unhealthy_regex).sum()
                failure_rate = failures / total_rows

    mom_growth = 0
    date_col = bus_term.get("primary_date")
    if not date_col:
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0:
            date_col = date_cols[0]
            
    if date_col and date_col in df.columns and main_num:
        temp_df = df.copy()
        temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors='coerce')
        temp_df = temp_df.dropna(subset=[date_col])
        if len(temp_df) > 0:
            monthly = temp_df.groupby(temp_df[date_col].dt.to_period("M"))[main_num].sum().reset_index()
            if len(monthly) >= 2:
                monthly = monthly.sort_values(date_col)
                last_month = monthly.iloc[-1][main_num]
                prev_month = monthly.iloc[-2][main_num]
                if prev_month > 0:
                    mom_growth = (last_month - prev_month) / prev_month

    stddev_ratio = 0
    if main_num:
        mean_val = df[main_num].mean()
        std_val = df[main_num].std()
        if mean_val > 0:
            stddev_ratio = std_val / mean_val

    # Apply rules
    RECOMMENDATION_RULES = [
        {
            "condition": lambda: top_category_share > 0.20,
            "title": f"Diversify dependency on top {main_cat or 'category'}",
            "rationale": f"The top category ({top_cat_name}) accounts for {top_category_share*100:.1f}% of total {main_num or 'volume'}. Diversification will balance distribution risk.",
            "priority": "High" if top_category_share > 0.4 else "Medium",
            "category": "risk"
        },
        {
            "condition": lambda: failure_rate > 0.02,
            "title": "Investigate transaction failure rate",
            "rationale": f"The failure rate in {status_col or 'transactions'} is {failure_rate*100:.1f}%. Streamline processing workflow to improve success rate.",
            "priority": "High",
            "category": "operations"
        },
        {
            "condition": lambda: abs(mom_growth) > 0.05,
            "title": "Address Month-over-Month volume trend",
            "rationale": f"Month-over-month {main_num or 'volume'} changed by {mom_growth*100:.1f}%. Track drivers to sustain performance.",
            "priority": "Medium",
            "category": "trend"
        },
        {
            "condition": lambda: stddev_ratio > 1.0,
            "title": f"Manage volatility in {main_num or 'metric'}",
            "rationale": f"Standard deviation to mean ratio for {main_num or 'metric'} is {stddev_ratio:.2f}, indicating volume variance.",
            "priority": "Medium",
            "category": "anomaly"
        }
    ]

    matched_rules = []
    for rule in RECOMMENDATION_RULES:
        if rule["condition"]():
            matched_rules.append({
                "title": rule["title"],
                "rationale": rule["rationale"],
                "priority": rule["priority"],
                "category": rule["category"]
            })

    # Always ensure at least 3 high-quality actionable recommendations using dataset fallbacks
    if len(matched_rules) < 3:
        fallbacks = [
            {
                "title": f"Scale operations in primary metric ({main_num or 'volume'})",
                "rationale": f"Evaluated {len(df):,} active records. Focus on expanding operational throughput in top-performing segments.",
                "priority": "High",
                "category": "growth"
            },
            {
                "title": "Establish automated data quality & completeness monitoring",
                "rationale": f"Audit dataset fields routinely to ensure zero missing entries across key dimensions.",
                "priority": "Medium",
                "category": "data_quality"
            },
            {
                "title": "Optimize category resource allocation",
                "rationale": f"Align capacity with high-volume transaction channels to maximize overall revenue and efficiency.",
                "priority": "Medium",
                "category": "operations"
            }
        ]
        for fb in fallbacks:
            if len(matched_rules) >= 4:
                break
            if not any(r["title"] == fb["title"] for r in matched_rules):
                matched_rules.append(fb)

    # 3. LLM Translation with Deterministic Fallback (each item zero-trust verified individually)
    recs = []
    api_key = os.getenv("GROQ_API_KEY")

    if api_key and api_key.strip():
        prompt = f"""Given these deterministically generated recommendation rules based on the user's data for the business domain '{domain}':
{json.dumps(matched_rules)}

Your task is ONLY to polish the wording of these recommendations.
CRITICAL: Do NOT invent new recommendations. Only polish the ones provided.
CRITICAL: Do NOT change the recommendation category or priority.
CRITICAL: Do NOT invent or change any numbers.
CRITICAL: Terminology MUST strictly match the detected business domain vocabulary.
Return ONLY a valid JSON array of objects, one per input rule in the SAME ORDER, with keys:
- title (string, action-oriented)
- rationale (string, explain why using the facts and EXACT numbers)
- priority (string, High, Medium, Low)
- category (string, one of: category_breakdown, trend, anomaly, risk, seasonality, operations, data_quality, growth)"""

        try:
            res = completion(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                api_key=api_key,
                max_tokens=2000
            )
            content = res.choices[0].message.content
            clean_content = content.strip()
            m = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
            if m:
                clean_content = m.group(1).strip()
            llm_recs = json.loads(clean_content)
            if not isinstance(llm_recs, list) or len(llm_recs) != len(matched_rules):
                raise ValueError(f"LLM returned {len(llm_recs) if isinstance(llm_recs, list) else type(llm_recs)} items, expected {len(matched_rules)}")

            for original, r in zip(matched_rules, llm_recs):
                rationale = r.get("rationale", "") if isinstance(r, dict) else ""
                passed = bool(rationale.strip()) and verify_numbers_against_facts(rationale, original["rationale"])
                if passed:
                    r["verified"] = True
                    recs.append(r)
                else:
                    logging.warning(f"[recommendations] Zero-trust numeric check failed for '{original['title']}'. Falling back to deterministic template.")
                    fallback = dict(original)
                    fallback["verified"] = False
                    recs.append(fallback)
        except Exception as e:
            logging.warning(f"[recommendations] LLM call/parse failed: {e}. Using deterministic fallback.")
            recs = [dict(r, verified=False) for r in matched_rules]
    else:
        recs = [dict(r, verified=False) for r in matched_rules]

    if not recs:
        recs = [dict(r, verified=False) for r in matched_rules]

    # 4. Accuracy Check & Save (Clear old recommendations first on refresh)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM recommendations WHERE user_id = %s AND dataset_id = %s", (current_user["id"], dataset_info["id"]))
    except Exception as del_err:
        logging.error(f"Failed to clear old recommendations: {del_err}")

    final_recs = []

    for r in recs:
        rec_id = f"rec_{uuid.uuid4().hex[:8]}"
        created_at = datetime.utcnow().isoformat()
        is_verified = bool(r.get("verified", False))

        cursor.execute('''
            INSERT INTO recommendations (id, user_id, dataset_id, title, rationale, priority, category, verified, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            rec_id,
            current_user["id"],
            dataset_info["id"],
            r.get("title", "Recommendation"),
            r.get("rationale", ""),
            r.get("priority", "Medium"),
            r.get("category", "operations"),
            1 if is_verified else 0,
            created_at
        ))

        r["id"] = rec_id
        r["verified"] = is_verified
        final_recs.append(r)
        
    conn.commit()
    conn.close()
    
    return final_recs
