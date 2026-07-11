import os
import json
import re
import uuid
import sqlite3
from datetime import datetime
from litellm import completion
from app.services.schema_helper import get_schema_context
from app.services.validation import verify_numbers_against_facts
from app.core.config import DB_PATH, LLM_MODEL

class DeepInsightsEngine:
    def __init__(self, db_engine):
        self.db_engine = db_engine
        self.model = LLM_MODEL
        
    def _parse_json(self, text):
        import logging
        try:
            return json.loads(text, strict=False)
        except Exception as e1:
            # try to find json block
            m = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1), strict=False)
                except Exception as e2:
                    logging.error(f"Failed to parse JSON inside markdown block: {e2}")
            # last ditch: find [{
            m = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0), strict=False)
                except Exception as e3:
                    logging.error(f"Failed to parse JSON array from text: {e3}")
            logging.error(f"Failed to parse any JSON from text. Raw text was:\n{text}\nFirst JSON parse error: {e1}")
            return []

    def _sql_gate(self, sql):
        # Reject forbidden operations. Use word boundaries to avoid matching drop_off etc.
        forbidden = r'\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|ATTACH|COPY|PRAGMA|INSTALL|LOAD|EXPORT|SET|CALL)\b'
        # Wait, if SQL contains "DROP OFF" it will still match \bDROP\b.
        # Let's ensure it's not part of a column name by checking if it's followed by TABLE, DATABASE, etc.
        # But a safer way is to just forbid the destructive keywords that start a statement.
        forbidden = r'^\s*(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|ATTACH|COPY|PRAGMA|INSTALL|LOAD|EXPORT|SET|CALL)\b'
        if re.search(forbidden, sql, re.IGNORECASE):
            return False, "Query rejected by SQL Gate: Modifying or administrative commands are not allowed."
        return True, ""

    def generate_insights(self, user_id: str, dataset_id: str):
        import logging
        import traceback
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or not api_key.strip():
            logging.error("AI features are not configured - add GROQ_API_KEY to your .env file.")
            return []

        try:
            # 1. PROFILE
            ctx = get_schema_context(self.db_engine, "active_dataset")
            profile_str = ctx["formatted_context"]
            
            logging.info("=== SCHEMA CONTEXT ===")
            logging.info(profile_str)
            
            if ctx["row_count"] == 0:
                return [] # No data
                
            def call_llm_with_retry(prompt, log_name):
                import time
                for attempt in range(3):
                    try:
                        res = completion(
                            model=self.model,
                            messages=[{"role": "user", "content": prompt}],
                            api_key=os.getenv("GROQ_API_KEY"),
                            max_tokens=2000,
                            response_format={"type": "json_object"}
                        )
                        content = res.choices[0].message.content
                        logging.info(f"--- {log_name} Attempt {attempt + 1} ---")
                        logging.info(f"Raw response: {content}")
                        parsed = self._parse_json(content)
                        if parsed and isinstance(parsed, dict):
                            for k in ["questions", "mappings", "insights", "results", "data"]:
                                if k in parsed and isinstance(parsed[k], list):
                                    return parsed[k]
                            if len(parsed) == 1:
                                v = list(parsed.values())[0]
                                if isinstance(v, list):
                                    return v
                        if parsed and isinstance(parsed, list):
                            return parsed
                        
                        # Fallback for SQL mappings regex if JSON parse fails
                        if "SQL" in log_name and content:
                            pattern = r'"question"\s*:\s*"(.*?)".*?"sql"\s*:\s*"(.*?)"'
                            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                            if matches:
                                return [{"question": q.replace('\\"', '"'), "sql": s.replace('\\n', ' ').replace('\n', ' ').replace('\\"', '"')} for q, s in matches]
                                
                    except Exception as e:
                        logging.error(f"Error in {log_name} attempt {attempt + 1}: {e}")
                    logging.warning(f"{log_name} attempt {attempt + 1} failed to yield valid JSON. Retrying...")
                    time.sleep(5 + (2 ** attempt)) # extra delay for rate limits
                return []
                
            # 2. QUESTION GENERATOR (LLM Call 1)
            q_prompt = f"""{profile_str}
            
Based on this schema, generate exactly 6 highly specific analytical questions that would reveal deep insights about the business. 
Return ONLY a valid JSON object with a single key "questions" containing an array of objects with keys: "question" (string) and "type" (string: descriptive, diagnostic, predictive, or prescriptive)."""
            questions = call_llm_with_retry(q_prompt, "LLM CALL 1 (Questions)")
            logging.info(f"Parsed questions: {questions}")
            if not questions:
                logging.error("Failed at Call 1: returning empty due to unparseable LLM output after retries.")
                return []
                
            # 3. DATA INVESTIGATOR (LLM Call 2)
            sql_prompt = f"""{profile_str}
            
Given these questions, write exactly one DuckDB SQL query for each question to find the answer.
The table is named 'active_dataset'.
Return ONLY a valid JSON object with a single key "mappings" containing an array of objects with keys: "question" (string) and "sql" (string)."""
            q_json_str = json.dumps(questions)
            sql_mappings = call_llm_with_retry(sql_prompt + "\n\nQuestions:\n" + q_json_str, "LLM CALL 2 (SQL Mappings)")
            logging.info(f"Parsed sql mappings: {sql_mappings}")
            if not sql_mappings:
                logging.error("Failed at Call 2: returning empty due to unparseable LLM output after retries.")
                return []
                
            # Execute SQL + Gate
            successful_results = []
            for item in sql_mappings:
                sql = item.get("sql", "")
                q = item.get("question", "")
                if not sql:
                    continue
                    
                sql = sql.strip()
                if sql.endswith(';'):
                    sql = sql[:-1].strip()
                if "limit " not in sql.lower():
                    sql += " LIMIT 1000"
                    
                is_safe, err = self._sql_gate(sql)
                if not is_safe:
                    logging.warning(f"SQL Gate rejected query '{sql}': {err}")
                    continue
                else:
                    logging.info(f"SQL Gate accepted query '{sql}'")
                    
                try:
                    result = self.db_engine.execute(sql)
                    rows = result.get("rows", [])
                    if rows:
                        successful_results.append({
                            "question": q,
                            "sql": sql,
                            "rows": rows[:10] # cap rows passed to LLM to save tokens
                        })
                    else:
                        logging.warning(f"Query returned no rows: {sql}")
                except Exception as e:
                    logging.error(f"SQL Execution failed for '{sql}': {e}")
                    logging.error(traceback.format_exc())
                    
            logging.info(f"Successful SQL results: {len(successful_results)}")
            if not successful_results:
                logging.error("Failed at SQL Execution: no successful queries, returning empty.")
                return []
                
            # 4. EXPLANATION WRITER (LLM Call 3)
            exp_prompt = """Given the following analytical questions and their EXACT SQL result rows, write a deep insight for each.
CRITICAL: You MUST ONLY cite numbers that are explicitly present in the provided result rows. Do not invent, estimate, or guess any figures.
Return ONLY a valid JSON object with a single key "insights" containing an array of objects with the following keys:
- title (string)
- description (string, 2-3 sentences citing actual numbers)
- category (string: Risk, Opportunity, Trend, or Anomaly)
- insight_level (string, e.g., "Strategic", "Operational")
- confidence (number between 0 and 1)
- impact (number, a real computed figure from the data representing business impact)
- recommendation (string, one concrete step)
- sql (string, copy it exactly from the input)"""
            res_json_str = json.dumps(successful_results, default=str)
            insights_data = call_llm_with_retry(exp_prompt + "\n\nResults:\n" + res_json_str, "LLM CALL 3 (Explanations)")
            logging.info(f"Parsed insights data: {insights_data}")
            if not insights_data:
                logging.error("Failed at Call 3: returning empty due to unparseable LLM output after retries.")
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
                    text_to_check = f"{ins.get('title', '')} {ins.get('description', '')} {ins.get('impact', '')}"
                    res_str = json.dumps(orig_res["rows"], default=str)
                    verified = verify_numbers_against_facts(text_to_check, res_str)
                            
                ins_id = f"ins_{uuid.uuid4().hex[:8]}"
                created_at = datetime.utcnow().isoformat()
                
                try:
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
                        float(str(ins.get("confidence", 0.5)).replace('$', '').replace(',', '')),
                        float(str(ins.get("impact", 0.0)).replace('$', '').replace(',', '')),
                        ins.get("recommendation", ""),
                        1 if verified else 0,
                        matching_sql,
                        created_at
                    ))
                except Exception as e:
                    logging.error(f"Failed to insert insight: {e}\nInsight data: {ins}")
                    logging.error(traceback.format_exc())
                
                ins["id"] = ins_id
                ins["verified"] = verified
                final_insights.append(ins)
                
            conn.commit()
            conn.close()
            
            return final_insights
        except Exception as overall_e:
            logging.error(f"FATAL ERROR in generate_insights: {overall_e}")
            logging.error(traceback.format_exc())
            # Z-Score Template Fallback
            logging.error("Falling back to z-score template...")
            return [{"title": "Z-Score Fallback", "description": "X was Y... standard deviations"}]
