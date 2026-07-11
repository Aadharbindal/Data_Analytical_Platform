import sys
sys.path.append("c:\\Users\\user\\Documents\\Data_Analytics\\ai-bi-os\\backend")
import logging
logging.basicConfig(level=logging.INFO)

from app.services.query.duckdb_engine import DuckDBEngine
from app.services.insights_engine import DeepInsightsEngine
from litellm import completion
import json

db_engine = DuckDBEngine()
db_engine.register_dataset("active_dataset", "data/6c7d6c39-4a46-4a54-8841-6bef83a66eca_food_delivery_FINAL_TEST.csv", format="csv")
engine = DeepInsightsEngine(db_engine)

import app.services.schema_helper as sh
ctx = sh.get_schema_context(db_engine, "active_dataset")
print(ctx)

profile_str = ctx["formatted_context"]
q_prompt = f"""{profile_str}

Based on this schema, generate exactly 6 highly specific analytical questions that would reveal deep insights about the business. 
Return ONLY a valid JSON array of objects with keys: "question" (string) and "type" (string: descriptive, diagnostic, predictive, or prescriptive)."""

res1 = completion(
    model=engine.model,
    messages=[{"role": "user", "content": q_prompt}],
    max_tokens=2000
)
print("--- CALL 1 ---")
print(res1.choices[0].message.content)

questions = engine._parse_json(res1.choices[0].message.content)
sql_prompt = f"""{profile_str}

Given these questions, write exactly one DuckDB SQL query for each question to find the answer.
The table is named 'active_dataset'.
Return ONLY a valid JSON array of objects with keys: "question" (string) and "sql" (string)."""

q_json_str = json.dumps(questions)
res2 = completion(
    model=engine.model,
    messages=[
        {"role": "user", "content": sql_prompt + "\n\nQuestions:\n" + q_json_str}
    ],
    max_tokens=2000
)
print("--- CALL 2 ---")
print(res2.choices[0].message.content)

sql_mappings = engine._parse_json(res2.choices[0].message.content)
for item in sql_mappings:
    sql = item.get("sql", "")
    print(f"SQL: {sql}")
    is_safe, err = engine._sql_gate(sql)
    print(f"SAFE: {is_safe}, ERR: {err}")
    if is_safe:
        try:
            res = db_engine.execute(sql)
            print(f"ROWS: {len(res.get('rows', []))}")
        except Exception as e:
            print(f"EXEC ERR: {e}")
