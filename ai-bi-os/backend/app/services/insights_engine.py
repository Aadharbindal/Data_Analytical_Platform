import os
import json
import re
import uuid
import sqlite3
import logging
import traceback
from datetime import datetime
from litellm import completion
from app.core.config import DB_PATH, LLM_MODEL
from app.services.insight_candidates import generate_candidates

class DeepInsightsEngine:
    def __init__(self, db_engine):
        self.db_engine = db_engine
        self.model = LLM_MODEL

    def _parse_json(self, text):
        try:
            return json.loads(text, strict=False)
        except Exception as e1:
            m = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1), strict=False)
                except Exception as e2:
                    logging.error(f"Failed to parse JSON inside markdown block: {e2}")
            m = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0), strict=False)
                except Exception as e3:
                    logging.error(f"Failed to parse JSON array from text: {e3}")
            return []

    def _format_currency(self, val):
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
                return f"₹{fval:,.2f}"
        except:
            return f"₹{val}"

    def generate_insights(self, user_id: str, dataset_id: str):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or not api_key.strip():
            logging.error("AI features are not configured.")
            return []

        try:
            from app.services.data_processing import get_active_dataset, get_dataframe
            dataset_info = get_active_dataset(user_id)
            if not dataset_info:
                return []

            sem_dict = dataset_info.get("semantic_dict", {})
            df = get_dataframe(dataset_id, user_id)
            
            if df is None or len(df) == 0:
                return []

            # 1. Deterministic Candidate Generation
            logging.info("Generating deterministic candidates...")
            candidates = generate_candidates(df, sem_dict)
            
            if not candidates:
                logging.warning("No candidates generated.")
                return []
                
            # 2. Deterministic Scoring
            SCORES = {
                "concentration": lambda c: min(c.get("share_pct", 0) / 10, 10),
                "failure_rate":  lambda c: min(c.get("rate_pct", 0) / 5, 10),
                "trend":         lambda c: min(abs(c.get("mom_pct", 0)) / 5, 10),
                "missing_data":  lambda c: 4
            }
            
            for c in candidates:
                c_type = c.get("type", "")
                c["score"] = SCORES.get(c_type, lambda x: 5)(c)
                
            ranked = sorted(candidates, key=lambda c: c["score"], reverse=True)[:5]
            
            # 3. LLM Zero-Trust Prompt
            prompt = f"""For each data finding below, write an insight narrative.
CRITICAL ZERO-TRUST RULE: You are STRICTLY FORBIDDEN from writing any digits, numbers, percentages, or currencies.
You MUST ONLY use the exact placeholders provided (e.g. {{{{entity}}}}, {{{{value}}}}). The system will substitute them.
If you write a raw digit (e.g. '5', '10%', '2023'), the insight will be rejected and deleted.
Do NOT write placeholders that do not exist in the candidates.

Candidates:
{json.dumps(ranked, indent=2)}

Return ONLY a valid JSON object with a single key "insights" containing an array of objects:
- title (string, use placeholders if needed)
- finding (string, the main insight narrative using ONLY placeholders)
- category (string: Risk, Opportunity, Trend, Anomaly, or Operational)
- impact (string, e.g. "{{{{sample_size}}}} transactions affected")
- recommendation (string, what to do about it)
"""
            logging.info("Calling LLM for Zero-Trust narratives...")
            res = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                api_key=api_key,
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            content = res.choices[0].message.content
            parsed = self._parse_json(content)
            
            llm_insights = parsed.get("insights", []) if isinstance(parsed, dict) else parsed
            if not llm_insights:
                return []

            final_insights = []
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            try:
                cursor.execute("DELETE FROM insights WHERE user_id = ? AND dataset_id = ?", (user_id, dataset_id))
                conn.commit()
            except Exception as e:
                logging.error(f"Failed to clear old insights: {e}")

            # 4. Zero-Trust Check & Substitution
            def render(text, cand):
                if not text: return text
                for k, v in cand.items():
                    if k == "value":
                        text = text.replace(f"{{{{{k}}}}}", self._format_currency(v))
                    else:
                        text = text.replace(f"{{{{{k}}}}}", str(v))
                return text

            for ins, cand in zip(llm_insights, ranked):
                raw_text = f"{ins.get('title','')} {ins.get('finding','')} {ins.get('impact','')} {ins.get('recommendation','')}"
                
                # Zero-Trust Digit Check!
                if re.search(r'\d', raw_text):
                    logging.warning(f"ZERO-TRUST VIOLATION: LLM hallucinated a digit. Dropping insight. Raw: {raw_text}")
                    continue
                    
                # Substitute Placeholders
                title = render(ins.get('title', ''), cand)
                finding = render(ins.get('finding', ''), cand)
                impact = render(ins.get('impact', ''), cand)
                rec = render(ins.get('recommendation', ''), cand)
                
                final_ins = {
                    "id": f"ins_{uuid.uuid4().hex[:8]}",
                    "user_id": user_id,
                    "dataset_id": dataset_id,
                    "title": title,
                    "description": finding,
                    "category": ins.get("category", "Trend"),
                    "insight_level": "Operational",
                    "confidence": 0.99, # 100% deterministic mathematically
                    "impact": impact,
                    "recommendation": rec,
                    "verified": 1,
                    "audit_sql": f"Deterministic Pandas Pipeline: {cand.get('type')}",
                    "score": cand.get("score", 0),
                    "dimension_type": cand.get("dimension", "generic"),
                    "created_at": datetime.utcnow().isoformat() + "Z"
                }
                
                cursor.execute('''
                    INSERT INTO insights (id, user_id, dataset_id, title, description, category, insight_level, confidence, impact, recommendation, verified, audit_sql, score, dimension_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    final_ins["id"], final_ins["user_id"], final_ins["dataset_id"],
                    final_ins["title"], final_ins["description"], final_ins["category"],
                    final_ins["insight_level"], final_ins["confidence"], final_ins["impact"],
                    final_ins["recommendation"], final_ins["verified"], final_ins["audit_sql"],
                    final_ins["score"], final_ins["dimension_type"], final_ins["created_at"]
                ))
                final_insights.append(final_ins)
                
            conn.commit()
            conn.close()
            logging.info(f"Successfully generated {len(final_insights)} zero-trust deterministic insights.")
            return final_insights
            
        except Exception as e:
            logging.error(f"Zero-Trust Engine failed: {e}")
            logging.error(traceback.format_exc())
            return []
