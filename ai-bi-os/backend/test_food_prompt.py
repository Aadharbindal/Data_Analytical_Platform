import pandas as pd
import numpy as np
import re
import json
import os
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

fp = 'data/6c7d6c39-4a46-4a54-8841-6bef83a66eca_food_delivery_FINAL_TEST.csv'
df = pd.read_csv(fp)

facts = []
cat_cols = df.select_dtypes(exclude=[np.number, 'datetime64']).columns
num_cols = df.select_dtypes(include=[np.number]).columns

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
        'type': 'Performance',
        'finding': f'Top performing {main_cat} is {top_cat[main_cat]} with {main_num} of {top_cat[main_num]}.'
    })
    facts.append({
        'type': 'Underperformance',
        'finding': f'Lowest performing {main_cat} is {bot_cat[main_cat]} with {main_num} of {bot_cat[main_num]}.'
    })

if not facts:
    facts.append({
        'type': 'General',
        'finding': f'Dataset has {len(df)} rows and {len(df.columns)} columns.'
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

try:
    res = completion(
        model=os.getenv('LLM_MODEL', 'groq/llama-3.1-8b-instant'),
        messages=[{'role': 'user', 'content': prompt}],
        api_key=os.getenv('GROQ_API_KEY'),
        max_tokens=2000
    )
    content = res.choices[0].message.content
    print('RAW CONTENT:', repr(content))
except Exception as e:
    import traceback
    print("API Error:", e)
    traceback.print_exc()
