import os
import json
import re
import uuid
import sqlite3
from datetime import datetime
from litellm import completion
from app.services.schema_helper import get_schema_context
from app.core.config import DB_PATH, LLM_MODEL

class DeepInsightsEngine:
    def __init__(self, db_engine):
        self.db_engine = db_engine
        self.model = LLM_MODEL
        
    def _parse_json(self, text):
        try:
            return json.loads(text)
        except:
            # try to find json block
            m = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1))
                except:
                    pass
            # last ditch: find [{
            m = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0))
                except:
                    pass
            return []

    def _sql_gate(self, sql):
        # Reject forbidden operations
        forbidden = r'\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|ATTACH|COPY|PRAGMA|INSTALL|LOAD|EXPORT|SET)\b'
        if re.search(forbidden, sql, re.IGNORECASE):
            return False, "Query rejected by SQL Gate: Modifying or administrative commands are not allowed."
        return True, ""

    def generate_insights(self, user_id: str, dataset_id: str):
        # 1. PROFILE
        ctx = get_schema_context(self.db_engine, "active_dataset")
        profile_str = ctx["formatted_context"]
        
        if ctx["row_count"] == 0:
            return [] # No data
            
        # 2. QUESTION GENERATOR (LLM Call 1)
        q_prompt = f"""{profile_str}
        
Based on this schema, generate exactly 6 highly specific analytical questions that would reveal deep insights about the business. 
Return ONLY a valid JSON array of objects with keys: "question" (string) and "type" (string: descriptive, diagnostic, predictive, or prescriptive)."""
        
        res1 = completion(
            model=self.model,
            messages=[{"role": "user", "content": q_prompt}],
            api_key=os.getenv("GROQ_API_KEY")
        )
        questions = self._parse_json(res1.choices[0].message.content)
        if not questions:
            return []
            
        # 3. DATA INVESTIGATOR (LLM Call 2)
        sql_prompt = f"""{profile_str}
        
Given these questions, write exactly one DuckDB SQL query for each question to find the answer.
The table is named 'active_dataset'.
Return ONLY a valid JSON array of objects with keys: "question" (string) and "sql" (string)."""
        
        q_json_str = json.dumps(questions)
        res2 = completion(
            model=self.model,
            messages=[
                {"role": "user", "content": sql_prompt},
                {"role": "user", "content": q_json_str}
            ],
            api_key=os.getenv("GROQ_API_KEY")
        )
        sql_mappings = self._parse_json(res2.choices[0].message.content)
        if not sql_mappings:
            return []
            
        # Execute SQL + Gate
        successful_results = []
        for item in sql_mappings:
            sql = item.get("sql", "")
            q = item.get("question", "")
            if not sql:
                continue
                
            # Force LIMIT 1000
            if "limit " not in sql.lower():
                sql += " LIMIT 1000"
                
            is_safe, err = self._sql_gate(sql)
            if not is_safe:
                continue
                
            try:
                result = self.db_engine.execute(sql)
                rows = result.get("rows", [])
                if rows:
                    successful_results.append({
                        "question": q,
                        "sql": sql,
                        "rows": rows[:10] # cap rows passed to LLM to save tokens
                    })
            except Exception as e:
                # We skip retry to strictly enforce the 3 batched LLM calls max.
                pass
                
        if not successful_results:
            return []
            
        # 4. EXPLANATION WRITER (LLM Call 3)
        exp_prompt = """Given the following analytical questions and their EXACT SQL result rows, write a deep insight for each.
CRITICAL: You MUST ONLY cite numbers that are explicitly present in the provided result rows. Do not invent, estimate, or guess any figures.
Return ONLY a valid JSON array of objects with the following keys:
- title (string)
- description (string, 2-3 sentences citing actual numbers)
- category (string: Risk, Opportunity, Trend, or Anomaly)
- insight_level (string, e.g., "Strategic", "Operational")
- confidence (number between 0 and 1)
- impact (number, a real computed figure from the data representing business impact)
- recommendation (string, one concrete step)
- sql (string, copy it exactly from the input)"""

        res_json_str = json.dumps(successful_results, default=str)
        res3 = completion(
            model=self.model,
            messages=[
                {"role": "user", "content": exp_prompt},
                {"role": "user", "content": res_json_str}
            ],
            api_key=os.getenv("GROQ_API_KEY")
        )
        insights_data = self._parse_json(res3.choices[0].message.content)
        if not insights_data:
            return []
            
        # 5. ACCURACY CHECK & PERSIST
        final_insights = []
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        for ins in insights_data:
            # find matching result rows
            matching_sql = ins.get("sql", "")
            orig_res = next((r for r in successful_results if r["sql"] == matching_sql), None)
            
            verified = False
            if orig_res:
                # Extract all numbers from LLM text
                text_to_check = f"{ins.get('title', '')} {ins.get('description', '')} {ins.get('impact', '')}"
                llm_nums = re.findall(r'\b\d+(?:\.\d+)?\b', text_to_check.replace(',', ''))
                
                # Extract all numbers from result rows
                res_str = json.dumps(orig_res["rows"], default=str).replace(',', '')
                res_nums = re.findall(r'\b\d+(?:\.\d+)?\b', res_str)
                
                # We consider verified if every number in LLM output is found in the result
                # OR if there are no numbers in the LLM output (though prompt asks for numbers)
                verified = True
                for num_str in llm_nums:
                    try:
                        num = float(num_str)
                        if num == 0: continue # ignore 0
                        # allow slight rounding matches
                        match_found = False
                        for r_num_str in res_nums:
                            try:
                                if abs(float(r_num_str) - num) < 1.0:
                                    match_found = True
                                    break
                            except:
                                pass
                        if not match_found:
                            verified = False
                            break
                    except:
                        pass
                        
            ins_id = f"ins_{uuid.uuid4().hex[:8]}"
            created_at = datetime.utcnow().isoformat()
            
            cursor.execute('''
                INSERT INTO insights (id, user_id, dataset_id, title, description, category, insight_level, confidence, impact, recommendation, verified, audit_sql, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ins_id,
                user_id,
                dataset_id,
                ins.get("title", "Insight"),
                ins.get("description", ""),
                ins.get("category", "Trend"),
                ins.get("insight_level", "Operational"),
                float(ins.get("confidence", 0.5)),
                float(ins.get("impact", 0.0)),
                ins.get("recommendation", ""),
                1 if verified else 0,
                matching_sql,
                created_at
            ))
            
            ins["id"] = ins_id
            ins["verified"] = verified
            final_insights.append(ins)
            
        conn.commit()
        conn.close()
        
        return final_insights
