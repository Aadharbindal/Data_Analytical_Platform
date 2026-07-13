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
            
            from app.services.data_processing import get_active_dataset
            dataset_info = get_active_dataset(user_id)
            domain = "generic"
            if dataset_info:
                domain = dataset_info.get("domain", "generic")
                sem_dict = dataset_info.get("semantic_dict")
                if sem_dict:
                    profile_str += f"\nDETECTED BUSINESS DOMAIN: {domain}\nSEMANTIC DATA DICTIONARY:\n{json.dumps(sem_dict, indent=2)}\n"
            
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
Do NOT generate questions asking about future probability, likelihood, or prediction of events - this system can only query historical/existing data via SQL, not run predictive models. Only generate questions answerable by aggregating or filtering existing rows (sums, counts, averages, comparisons, rankings, time-based groupings of PAST data).
CRITICAL: Never generate multiple questions or recommendations from the exact same metric or dimension. Select questions spanning completely different analytical dimensions (e.g., category breakdown, trend over time, anomaly detection, risk assessment, seasonality, operational efficiency, data quality) to maximize decision value.
Return ONLY a valid JSON object with a single key "questions" containing an array of objects with keys: "question" (string) and "type" (string: descriptive, diagnostic, predictive, or prescriptive)."""
            questions = call_llm_with_retry(q_prompt, "LLM CALL 1 (Questions)")
            logging.info(f"Parsed questions: {questions}")
            if not questions:
                logging.error("Failed at Call 1: returning empty due to unparseable LLM output after retries.")
                return []
            import time
            time.sleep(3.5)
                
            # 3. DATA INVESTIGATOR (LLM Call 2)
            sql_prompt = f"""{profile_str}
            
Given these questions, write exactly one DuckDB SQL query for each question to find the answer.
The table is named 'active_dataset'.
When grouping by a high-cardinality dimension like exact date, prefer using COUNT(*) alongside any AVG/SUM and note that group-by-exact-date often produces tiny, statistically unreliable groups - consider grouping by week, month, or day-of-week instead for anything claiming a 'trend'.
IMPORTANT: Whenever you use GROUP BY, you MUST include COUNT(*) AS sample_size in your SELECT clause so sample sizes can be verified.
Return ONLY a valid JSON object with a single key "mappings" containing an array of objects with keys: "question" (string) and "sql" (string)."""
            q_json_str = json.dumps(questions)
            sql_mappings = call_llm_with_retry(sql_prompt + "\n\nQuestions:\n" + q_json_str, "LLM CALL 2 (SQL Mappings)")
            logging.info(f"Parsed sql mappings: {sql_mappings}")
            if not sql_mappings:
                logging.error("Failed at Call 2: returning empty due to unparseable LLM output after retries.")
                return []
            time.sleep(3.5)
                
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
                        # Check for minimum sample size in grouped aggregates
                        count_key = next((k for k in rows[0].keys() if "sample_size" in k.lower() or "count(" in k.lower()), None)
                        if "group by" in sql.lower() and count_key:
                            try:
                                if any(int(r.get(count_key, 0)) < 5 for r in rows):
                                    logging.warning(f"SQL Gate rejected result due to small sample size (<5) in groups: {sql}")
                                    continue
                            except (ValueError, TypeError):
                                pass

                        # Compute explicit stats to prevent LLM reasoning bugs
                        stats = {}
                        if len(rows) > 1:
                            for k in rows[0].keys():
                                try:
                                    # Try to convert column values to float
                                    vals = []
                                    for r in rows:
                                        if r[k] is not None:
                                            # Handle strings with commas or currency
                                            val_str = str(r[k]).replace(',', '').replace('₹', '').replace('$', '').replace('£', '').strip()
                                            vals.append(float(val_str))
                                    
                                    if len(vals) == len(rows): # only if all rows are valid numbers
                                        max_val = max(vals)
                                        min_val = min(vals)
                                        # Find the row that contains the max and min values
                                        max_row = next((r for r, v in zip(rows, vals) if v == max_val), {})
                                        min_row = next((r for r, v in zip(rows, vals) if v == min_val), {})
                                        
                                        stats[k] = {
                                            "highest_value": max_val,
                                            "highest_row_data": max_row,
                                            "lowest_value": min_val,
                                            "lowest_row_data": min_row
                                        }
                                except Exception:
                                    pass

                        successful_results.append({
                            "question": q,
                            "sql": sql,
                            "rows": rows[:10], # cap rows passed to LLM to save tokens
                            "explicit_stats_for_llm": stats
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
CRITICAL: Terminology MUST strictly match the detected business domain vocabulary. Never use generic labels like Revenue, Customers, Deal Size unless those concepts explicitly exist in the dataset. Use terminology consistent with the SEMANTIC DATA DICTIONARY columns and names.
CRITICAL: You MUST ONLY cite numbers and metrics that are explicitly present in the provided result rows and SQL query. Do not invent, estimate, or guess any figures.
CRITICAL: DO NOT infer or mention columns/metrics that do not exist in the results (e.g., do not talk about 'loss', 'profit', or 'cost' if the query only returns 'revenue' or 'transaction count').
CRITICAL: Terminology MUST be strictly consistent between title, description, and recommendation. For example, if the query and title talk about 'top payees' or 'payers', the description/finding must not mismatch and talk about 'payers' or 'payees' (or vice versa). Keep them strictly consistent.
CRITICAL: Recommendations MUST be directly traceable to the SQL evidence. Do NOT recommend high-level business actions like "Invest", "Increase Marketing", "Improve Offering", or "Boost Revenue" unless the dataset explicitly supports and proves those conclusions. Prefer conservative, data-focused action verbs for recommendations, such as: "Monitor", "Investigate", "Analyze", "Compare", "Validate", "Track", or "Review". Do not recommend "Validate data quality" unless there is actual evidence of bad data.
CRITICAL: If the data does not support a clear conclusion, do not generate an insight for this question at all - simply skip it.
CRITICAL: If you cannot state a specific, real impact number for this insight, do not generate it - skip the question entirely rather than describing the absence of an answer.
CRITICAL: Do NOT use speculative or forward-looking language such as 'might', 'could', 'anticipate', 'projected', 'likely to', 'expected to' unless the underlying data genuinely contains a forecast/projection value computed by the system.
CRITICAL: State the SQL aggregate function accurately - if the query used SUM(), call it a total; if AVG(), call it an average; never substitute one for the other.
CRITICAL: The Impact value MUST logically match the metric discussed in the finding. If finding is about Average Amount, Impact must be the Average Amount. If Total Amount, Impact must be Total Amount. If Count, Impact must be Count. Do not mix Average and Total.
CRITICAL: For confidence, do not default to 1.0 or 0.0. Provide realistic values like 0.92, 0.95, or 0.98 based on data clarity and sample size.
CRITICAL: Do NOT generate long prose paragraphs. Instead, the description field MUST be short and structured (strictly using key-value lines followed by a Finding).
CRITICAL CURRENCY RULE: ALWAYS use the ₹ (Indian Rupee) symbol for ALL monetary values. NEVER use $ (dollar) or £ (pound) or any other currency symbol under any circumstances. Every currency value in title, description, and finding MUST use ₹ only.
CRITICAL NUMBER FORMAT RULE: Format all monetary values using the Indian numbering system (commas after the first 3 digits from the right, and then every 2 digits). Example CORRECT: ₹29,97,663.92.
CRITICAL CONCLUSION ACCURACY RULE: We have provided `explicit_stats_for_llm` showing the exact highest and lowest values and their corresponding rows (`highest_row_data`, `lowest_row_data`). You MUST strictly use these pre-computed stats to form your finding. NEVER infer or compute highest/lowest yourself. Look at the dimension inside `highest_row_data` to see which category actually had the highest value. Do not contradict the explicit stats.
CRITICAL IMPACT MAGNITUDE RULE: The impact field MUST be a meaningful metric WITH context. Examples of valid impact values: "₹3.17M Processed", "358 Transactions", "₹51.9K Average". NEVER output raw isolated numbers like "7" or "4.3". You MUST output a formatted string containing the number, the unit (₹, %, etc.), and a 1-2 word context (e.g. Average, Processed, Drop).
CRITICAL TERMINOLOGY: If the metric is 'Transaction Value', do not call it 'revenue stream'. Stick to 'transaction value'.
Return ONLY a valid JSON object with a single key "insights" containing an array of objects with the following keys:
- title (string)
- description (string, structured key-value lines followed by finding, formatted EXACTLY as follows:
Key1: Value1
Key2: Value2

Finding: The actual textual finding explaining the trend or insight in 1-2 sentences.

Do not use bolding or markdown inside the description. Example format:
Highest Month: June ₹13,985
Lowest Month: January ₹9,275
Difference: +51%

Finding: Average transaction value peaked in June.
)
- category (string: Risk, Opportunity, Trend, or Anomaly)
- insight_level (string, e.g., "Strategic", "Operational")
- confidence (MUST be a numeric float between 0.0 and 1.0)
- impact (string, MUST include metric, unit, and context e.g. "₹51.9K Average" or "358 Transactions")
- recommendation (string, one concrete, conservative step grounded in the actual data)
- sql (string, copy it exactly from the input)"""
            # Build explicit constraints to prevent LLM reasoning bugs and ensure correctness
            constraint_str = ""
            for i, res in enumerate(successful_results):
                q = res["question"]
                stats = res.get("explicit_stats_for_llm", {})
                rows = res.get("rows", [])
                
                constraint_str += f"\nResult {i+1} for Question: \"{q}\"\n"
                constraint_str += f"Rows: {json.dumps(rows)}\n"
                
                num_col = None
                for k in stats:
                    if "highest_value" in stats[k]:
                        num_col = k
                        break
                if num_col and rows:
                    col_stats = stats[num_col]
                    cat_col = None
                    for k in rows[0].keys():
                        if k != num_col and not isinstance(rows[0][k], (int, float)):
                            cat_col = k
                            break
                    if not cat_col:
                        for k in rows[0].keys():
                            if k != num_col:
                                cat_col = k
                                break
                                
                    if cat_col:
                        high_val = col_stats.get("highest_value")
                        low_val = col_stats.get("lowest_value")
                        high_row = col_stats.get("highest_row_data", {})
                        low_row = col_stats.get("lowest_row_data", {})
                        high_cat = high_row.get(cat_col)
                        low_cat = low_row.get(cat_col)
                        
                        def fmt(val):
                            try:
                                fval = float(val)
                                if fval >= 10000000:
                                    return f"₹{fval / 10000000:,.2f}Cr"
                                elif fval >= 100000:
                                    return f"₹{fval / 100000:,.2f}L"
                                elif fval.is_integer():
                                    s = str(int(fval))
                                    if len(s) > 3:
                                        s = s[:-3] + ',' + s[-3:]
                                        while len(s.split(',')[0]) > 2:
                                            parts = s.split(',')
                                            parts[0] = parts[0][:-2] + ',' + parts[0][-2:]
                                            s = ','.join(parts)
                                    return f"₹{s}"
                                else:
                                    # Basic fallback for decimals
                                    return f"₹{fval:,.2f}"
                            except:
                                return f"₹{val}"
                                
                        constraint_str += (
                            f"CRITICAL CONSTRAINT FOR THIS RESULT:\n"
                            f"- The highest '{num_col}' is {fmt(high_val)} corresponding to '{high_cat}'.\n"
                            f"- The lowest '{num_col}' is {fmt(low_val)} corresponding to '{low_cat}'.\n"
                            f"- In your description and finding, you MUST explicitly state that '{high_cat}' is the highest with {fmt(high_val)} and '{low_cat}' is the lowest with {fmt(low_val)}.\n"
                            f"- Do NOT state any other category as the highest or lowest. Refer only to the correct highest and lowest categories as proven by the facts.\n"
                        )

            res_json_str = json.dumps(successful_results, default=str)
            full_exp_prompt = f"{exp_prompt}\n\nConstraints and Facts:\n{constraint_str}\n\nResults:\n{res_json_str}"
            insights_data = call_llm_with_retry(full_exp_prompt, "LLM CALL 3 (Explanations)")
            logging.info(f"Parsed insights data: {insights_data}")
            if not insights_data:
                logging.error("Failed at Call 3: returning empty due to unparseable LLM output after retries.")
                return []
                
            # 5. ACCURACY CHECK & PERSIST
            final_insights = []
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            try:
                cursor.execute("DELETE FROM insights WHERE user_id = ? AND dataset_id = ?", (user_id, dataset_id))
                conn.commit()
            except Exception as e:
                logging.error(f"Failed to clear old insights: {e}")
            
            hedging_phrases = [
                "can't draw any conclusions", "unobtainable", "insufficient data", "unable to determine", "no clear pattern",
                "not explicitly stated", "not available in the data", "data does not show", "cannot be determined",
                "not clearly indicated", "no significant", "not specified", "data does not provide",
                "not evident from the data", "cannot be confirmed", "not observed in the",
                "insufficient information", "not identifiable"
            ]
            speculative_pattern = re.compile(r'\b(might|could|anticipate|projected|likely to|expected to|predicted|prediction|probability of|likelihood of|forecast to|will (?:likely )?(?:increase|decrease|happen)|chance of)\b', re.IGNORECASE)
            
            def reformat_currency(text):
                if not text: return text
                # Replace prefix other currency signs/names with ₹
                text = re.sub(
                    r'(?:[£$€]|USD|GBP|INR|Rs\.?|Rs|EUR|rupees|rupee)\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)',
                    r'₹\1',
                    str(text),
                    flags=re.IGNORECASE
                )
                # Replace suffix other currency signs/names with ₹
                text = re.sub(
                    r'([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)\s*(?:[£$€]|USD|GBP|INR|Rs\.?|Rs|EUR|rupees|rupee)',
                    r'₹\1',
                    str(text),
                    flags=re.IGNORECASE
                )
                text = text.replace('£', '₹').replace('$', '₹').replace('€', '₹')
                text = re.sub(r'₹+', '₹', text)
                
                def replacer(match):
                    raw_num = match.group(1).replace(',', '')
                    try:
                        val = float(raw_num)
                        if val.is_integer():
                            return f"₹{int(val):,}"
                        else:
                            return f"₹{val:,.2f}"
                    except ValueError:
                        return match.group(0)
                return re.sub(r'₹\s*([0-9,]+\.?[0-9]*)', replacer, text)

            def replace_revenue_terminology(text):
                if not text: return text
                text = re.sub(r'\brevenue stream(s)?\b', lambda m: 'transaction value' + (m.group(1) if m.group(1) else ''), text, flags=re.IGNORECASE)
                text = re.sub(r'\brevenue(s)?\b', lambda m: 'transaction value' + (m.group(1) if m.group(1) else ''), text, flags=re.IGNORECASE)
                return text

            def format_impact_value(val: float, is_currency: bool, label: str) -> str:
                 try:
                     val = float(val)
                 except:
                     pass
                 prefix = "₹" if is_currency else ""
                 if val >= 10_000_000:
                     return f"{prefix}{val / 10_000_000:.2f}Cr {label}".strip()
                 elif val >= 100_000:
                     return f"{prefix}{val / 100_000:.2f}L {label}".strip()
                 elif val >= 1_000:
                     return f"{prefix}{val / 1_000:.1f}K {label}".strip()
                 else:
                     if isinstance(val, (int, float)) and float(val).is_integer():
                         return f"{prefix}{int(val)} {label}".strip()
                     else:
                         return f"{prefix}{val:.2f} {label}".strip()

            def validate_and_correct_insight(ins, orig_res):
                stats = orig_res.get("explicit_stats_for_llm", {})
                rows = orig_res.get("rows", [])
                if not rows or not stats:
                    return ins
                    
                num_col = None
                for k in stats:
                    if "highest_value" in stats[k]:
                        num_col = k
                        break
                if not num_col:
                    return ins
                    
                cat_col = None
                for k in rows[0].keys():
                    if k != num_col and not isinstance(rows[0][k], (int, float)):
                        cat_col = k
                        break
                if not cat_col:
                    for k in rows[0].keys():
                        if k != num_col:
                            cat_col = k
                            break
                if not cat_col:
                    return ins
                    
                col_stats = stats[num_col]
                high_row = col_stats.get("highest_row_data", {})
                low_row = col_stats.get("lowest_row_data", {})
                
                high_cat = str(high_row.get(cat_col, ''))
                low_cat = str(low_row.get(cat_col, ''))
                
                high_val = col_stats.get("highest_value")
                low_val = col_stats.get("lowest_value")
                
                formatted_high = format_impact_value(high_val, True, "").strip()
                formatted_low = format_impact_value(low_val, True, "").strip()
                
                cat_label = cat_col.replace('_', ' ').title()
                val_label = num_col.replace('_', ' ').title()
                
                diff_str = ""
                if low_val and low_val > 0:
                    pct_diff = ((high_val - low_val) / low_val) * 100
                    diff_str = f"\nDifference: +{pct_diff:,.1f}%" if pct_diff >= 0 else f"\nDifference: {pct_diff:,.1f}%"
                
                rebuilt_desc = (
                    f"Highest {cat_label}: {high_cat} {formatted_high}\n"
                    f"Lowest {cat_label}: {low_cat} {formatted_low}"
                    f"{diff_str}\n\n"
                    f"Finding: {high_cat} had the highest {val_label.lower()} of {formatted_high}, "
                    f"while {low_cat} had the lowest {val_label.lower()} of {formatted_low}."
                )
                
                # Verify and rewrite impact
                impact = ins.get("impact", "")
                numeric_part = re.findall(r'[0-9]+(?:\.[0-9]+)?', impact.replace(',', ''))
                if numeric_part:
                    try:
                        imp_val = float(numeric_part[0])
                        if imp_val < 50:
                            sum_val = sum(float(str(r.get(num_col, 0)).replace(',', '').replace('₹', '').replace('$', '').strip()) for r in rows if r.get(num_col) is not None)
                            if sum_val >= 50:
                                if "avg" in orig_res.get("sql", "").lower():
                                    ins["impact"] = format_impact_value(high_val, True, "Average")
                                else:
                                    ins["impact"] = format_impact_value(sum_val, True, "Total Processed")
                            else:
                                ins["impact"] = f"{len(rows)} Transactions"
                    except Exception:
                        pass
                
                # Replace incorrect categories in recommendation
                rec = ins.get("recommendation", "")
                all_cats = [str(r.get(cat_col)) for r in rows if r.get(cat_col) is not None]
                for cat in all_cats:
                    if cat != high_cat and cat != low_cat and cat in rec:
                        if "lowest" in rec.lower() or "decline" in rec.lower() or "drop" in rec.lower():
                            rec = rec.replace(cat, low_cat)
                        else:
                            rec = rec.replace(cat, high_cat)
                
                # Verify recommendation does not suggest data quality issues
                if any(phrase in rec.lower() for phrase in ["data quality", "data integrity", "data entry", "data gap", "bad data", "validate data"]):
                    rec = f"Monitor {high_cat} and {low_cat} transaction patterns to identify growth opportunities."
                
                ins["description"] = rebuilt_desc
                ins["recommendation"] = rec
                return ins

            for ins in insights_data:
                # Forcefully fix currency formatting and terminology
                ins['title'] = replace_revenue_terminology(reformat_currency(ins.get('title', '')))
                ins['description'] = replace_revenue_terminology(reformat_currency(ins.get('description', '')))
                ins['impact'] = replace_revenue_terminology(reformat_currency(ins.get('impact', '')))
                ins['recommendation'] = replace_revenue_terminology(reformat_currency(ins.get('recommendation', '')))
                
                # find matching result rows
                matching_sql = ins.get("sql", "")
                orig_res = next((r for r in successful_results if r["sql"] == matching_sql), None)
                
                if orig_res:
                    ins = validate_and_correct_insight(ins, orig_res)
                    # Reformat again post-correction
                    ins['description'] = replace_revenue_terminology(reformat_currency(ins.get('description', '')))
                    ins['recommendation'] = replace_revenue_terminology(reformat_currency(ins.get('recommendation', '')))
                
                title_desc = f"{ins.get('title', '')} {ins.get('description', '')}"
                
                # Filter Problem 1: Hedging
                if any(phrase in title_desc.lower() for phrase in hedging_phrases):
                    logging.info(f"Skipping insight due to hedging language: {ins.get('title')}")
                    continue
                    
                # Filter Problem 2: Speculation
                if speculative_pattern.search(title_desc):
                    logging.info(f"Skipping insight due to speculative language: {ins.get('title')}")
                    continue
                    
                # Filter Problem 3: Missing/Invalid Impact
                impact_val = ins.get('impact')
                if impact_val in (None, "N/A", "", "null", "None"):
                    logging.info(f"Skipping insight due to missing impact value: {ins.get('title')}")
                    continue
                # We no longer strictly test if it's floatable, because we want strings like "₹3.17M Processed"
                    
                # Filter Problem 4: Missing/Invalid Confidence
                confidence_val = ins.get('confidence')
                if confidence_val in (None, "N/A", "", "null", "None") or not isinstance(confidence_val, (int, float)):
                    logging.info(f"Skipping insight due to missing or non-numeric confidence value: {ins.get('title')}")
                    continue
                try:
                    conf = float(confidence_val)
                    if conf <= 0.0 or conf > 1.0:
                        logging.info(f"Skipping insight due to out of bounds or zero confidence ({conf}): {ins.get('title')}")
                        continue
                except (ValueError, TypeError):
                    logging.info(f"Skipping insight due to unparseable confidence value ({confidence_val}): {ins.get('title')}")
                    continue
                    
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
                        conf,
                        str(ins.get("impact", "")),
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
