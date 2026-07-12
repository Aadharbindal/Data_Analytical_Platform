import asyncio
import json
import os
import re
from litellm import completion
from dotenv import load_dotenv
import pandas as pd
import numpy as np

load_dotenv()

def main():
    filepath = "data/c4157ce1-a1b6-4c38-bfdd-7316d5890d3c_office_supplies_sales_TEST3.csv"
    df = pd.read_csv(filepath)
    
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
    print("=== RAW LLM OUTPUT ===")
    print(content)
    print("======================")
    
    m = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
    if m:
        content = m.group(0)
    recs = json.loads(content)
    
    print("\n=== FACTS DICT ===")
    print(json.dumps(facts, indent=2))
    
    fact_str = json.dumps(facts).replace(',', '')
    fact_nums = re.findall(r'\b\d+(?:\.\d+)?\b', fact_str)
    print(f"\nExtracted Fact Nums: {fact_nums}")
    
    for i, r in enumerate(recs):
        print(f"\n--- Recommendation {i+1} ---")
        rec_str = f"{r.get('title', '')} {r.get('rationale', '')}"
        print(f"Raw Text: {rec_str}")
        rec_str_clean = rec_str.replace(',', '')
        rec_nums = re.findall(r'\b\d+(?:\.\d+)?\b', rec_str_clean)
        print(f"Extracted Nums: {rec_nums}")
        
        verified = True
        failed_num = None
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
                    failed_num = num
                    break
            except:
                pass
        
        print(f"Verified: {verified}" + (f" (Failed on {failed_num})" if not verified else ""))

if __name__ == "__main__":
    main()
