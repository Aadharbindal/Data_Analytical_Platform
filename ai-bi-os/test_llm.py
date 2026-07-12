import os, sys, json
from litellm import completion
from dotenv import load_dotenv

load_dotenv('backend/.env')

q_json_str = '''[{"question": "What is the month-over-month growth rate?", "type": "descriptive"}]'''
profile_str = 'Table active_dataset with columns Amount, Branch'
sql_prompt = f"""{profile_str}

Given these questions, write exactly one DuckDB SQL query for each question to find the answer.
The table is named 'active_dataset'.
Return ONLY a valid JSON array of objects with keys: "question" (string) and "sql" (string)."""

res2 = completion(
    model='groq/openai/gpt-oss-120b',
    messages=[
        {"role": "user", "content": sql_prompt + "\n\nQuestions:\n" + q_json_str}
    ],
    api_key=os.getenv('GROQ_API_KEY'),
    max_tokens=2000
)
print('res2 =', res2)
