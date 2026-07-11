import json
import os
import pandas as pd
import numpy as np
import re
from app.services.validation import verify_numbers_against_facts
from app.core.config import LLM_MODEL
from litellm import completion
from dotenv import load_dotenv
load_dotenv()

def get_facts(df):
    facts = []
    cat_cols = df.select_dtypes(exclude=[np.number, 'datetime64']).columns
    num_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(cat_cols) > 0 and len(num_cols) > 0:
        main_cat = cat_cols[0]
        main_num = num_cols[0]
        for col in num_cols:
            if re.search(r'revenue|sales|profit|amount|\bmrr\b|\barr\b|turnover|income|earnings|\bgmv\b|sales_amount|order_value|net_revenue|total_revenue', col, re.IGNORECASE):
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
    return facts, main_cat, main_num, grouped if 'grouped' in locals() else None

datasets = [
    "data/0cddbdbc-ba08-4b45-a582-c792e8f72b9e_electronics_sales_BIG.csv",
    "data/c4157ce1-a1b6-4c38-bfdd-7316d5890d3c_office_supplies_sales_TEST3.csv",
    "data/45a1b577-96de-4c8f-8d15-05d0af29d203_saas_subscriptions_TEST.csv"
]

import time

for fp in datasets:
    print(f"\n============================")
    print(f"Testing: {fp}")
    df = pd.read_csv(fp)
    facts, main_cat, main_num, grouped = get_facts(df)
    print("FACTS DICT:")
    print(json.dumps(facts, indent=2))
    
    prompt = f"""Given these hard facts computed from the user's data:
{json.dumps(facts)}

Generate 3 actionable business recommendations. 
CRITICAL: You MUST ONLY cite numbers that are explicitly present in the provided facts. Do not invent, estimate, or guess any figures.
Return ONLY a valid JSON array of objects with keys:
- title (string, action-oriented)
- rationale (string, explain why using the facts and EXACT numbers)
- priority (string, High, Medium, Low)
- category (string)"""

    res = completion(
        model=os.getenv("LLM_MODEL", "groq/openai/gpt-oss-120b"),
        messages=[{"role": "user", "content": prompt}],
        api_key=os.getenv("GROQ_API_KEY"),
        max_tokens=2000
    )
    content = res.choices[0].message.content
    m = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
    if m: content = m.group(0)
    
    try:
        recs = json.loads(content)
        for i, r in enumerate(recs):
            rec_str = f"{r.get('title', '')} {r.get('rationale', '')}"
            verified = verify_numbers_against_facts(rec_str, json.dumps(facts))
            print(f"\n--- Rec {i+1} ---")
            print(f"Text: {rec_str}")
            print(f"Verified via verify_numbers_against_facts: {verified}")
    except Exception as e:
        print(f"Failed to parse LLM JSON: {e}")
        
    print("\n[Independent Pandas Verification]")
    print(f"Top {main_cat}: {grouped.iloc[0][main_cat]} = {grouped.iloc[0][main_num]}")
    print(f"Bottom {main_cat}: {grouped.iloc[-1][main_cat]} = {grouped.iloc[-1][main_num]}")
    
    print("Sleeping for 60 seconds to avoid TPM limit...")
    time.sleep(60)
