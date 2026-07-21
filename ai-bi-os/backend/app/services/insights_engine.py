import os
import json
import re
import uuid
from app.core.database import get_db_connection
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

            # A concentration_risk_overlap candidate already carries the same
            # share_pct info as the plain "concentration" candidate for that
            # (dimension, entity), plus the failure-rate overlay - so the
            # plain version is now redundant and would otherwise compete for
            # the same "Risk" category slot.
            overlap_keys = {(c["dimension"], c["entity"]) for c in candidates if c.get("type") == "concentration_risk_overlap"}
            if overlap_keys:
                candidates = [
                    c for c in candidates
                    if not (c.get("type") == "concentration" and (c.get("dimension"), c.get("entity")) in overlap_keys)
                ]

            # 2. Deterministic Scoring
            SCORES = {
                "concentration": lambda c: min(c.get("share_pct", 0) / 10, 10),
                "failure_rate":  lambda c: min(c.get("rate_pct", 0) / 5, 10),
                "trend":         lambda c: min(abs(c.get("mom_pct", 0)) / 5, 10),
                "missing_data":  lambda c: 4,
                # Scores on HOW MUCH worse than the dataset average the top
                # entity is, since that gap is the actual finding.
                "concentration_risk_overlap": lambda c: min(10, (c.get("entity_failure_pct", 0) - c.get("dataset_failure_pct", 0)) / 3),
            }

            for c in candidates:
                c_type = c.get("type", "")
                c["score"] = SCORES.get(c_type, lambda x: 5)(c)

            # Diversity: CLAUDE.md requires every insight to come from a
            # distinct analytical dimension (never two "Risk" findings from
            # two different columns competing for the same slot). Instead of
            # blindly taking the top-5 by score - which can hand back 3 near-
            # identical concentration/risk findings if a dataset has several
            # skewed categorical columns - keep only the single
            # highest-scoring candidate per dimension bucket, and rank those.
            DIMENSION_BUCKETS = {
                "concentration": "concentration",
                "concentration_risk_overlap": "concentration_risk_overlap",
                "trend": "trend",
                "failure_rate": "failure_rate",
                "missing_data": "data_quality",
                "metric_summary": "operational",
                "record_volume": "operational",
            }
            best_per_bucket = {}
            for c in candidates:
                bucket = DIMENSION_BUCKETS.get(c.get("type", ""), c.get("type", "other"))
                if bucket not in best_per_bucket or c["score"] > best_per_bucket[bucket]["score"]:
                    best_per_bucket[bucket] = c

            ranked = sorted(best_per_bucket.values(), key=lambda c: c["score"], reverse=True)[:5]
            
            # 3. LLM Zero-Trust Prompt
            prompt = f"""For each data finding below, write an insight narrative.
CRITICAL ZERO-TRUST RULE: You are STRICTLY FORBIDDEN from writing any digits, numbers, percentages, or currencies.
You MUST ONLY use the exact placeholders provided (e.g. {{{{entity}}}}, {{{{value}}}}). The system will substitute them.
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
            llm_insights = []
            if api_key and api_key.strip():
                try:
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
                    llm_insights = parsed.get("insights", []) if isinstance(parsed, dict) else (parsed if isinstance(parsed, list) else [])
                except Exception as llm_err:
                    logging.warning(f"LLM insight narrative generation failed: {llm_err}. Using deterministic fallback.")

            # 4. Zero-Trust Check & Substitution with Deterministic Fallback
            def render(text, cand):
                if not text: return text
                for k, v in cand.items():
                    if k == "value":
                        text = text.replace(f"{{{{{k}}}}}", self._format_currency(v))
                    else:
                        text = text.replace(f"{{{{{k}}}}}", str(v))
                return text

            final_insights = []
            
            for i, cand in enumerate(ranked):
                ins = llm_insights[i] if i < len(llm_insights) and isinstance(llm_insights[i], dict) else {}
                raw_text = f"{ins.get('title','')} {ins.get('finding','')} {ins.get('impact','')} {ins.get('recommendation','')}"
                
                # Check if LLM output is present and clean
                is_valid_llm = bool(raw_text.strip())

                # Reject placeholders the LLM invented that don't exist for this
                # candidate (e.g. a "trend" candidate has no "entity" field, so
                # a title like "Decline in {{entity}}" would render as broken,
                # literal "{{entity}}" text shown to the user).
                if is_valid_llm:
                    unresolved = re.findall(r'\{\{(\w+)\}\}', raw_text)
                    if any(u not in cand for u in unresolved):
                        logging.warning(f"ZERO-TRUST WARNING: LLM used an unknown placeholder. Falling back to candidate template. Raw: {raw_text}")
                        is_valid_llm = False

                if is_valid_llm and re.search(r'\d', raw_text):
                    # Check if digits in raw_text are acceptable candidate values (e.g. year/period or entity name)
                    valid_digit_strs = [str(cand.get(k, '')) for k in ["period", "entity", "dimension"] if cand.get(k)]
                    has_unverified_digit = True
                    for num in re.findall(r'\d+', raw_text):
                        if any(num in v for v in valid_digit_strs):
                            has_unverified_digit = False
                            break
                    if has_unverified_digit:
                        logging.warning(f"ZERO-TRUST WARNING: LLM introduced digits. Falling back to candidate template. Raw: {raw_text}")
                        is_valid_llm = False

                c_type = cand.get("type", "generic")
                dim = cand.get("dimension", "dimension")
                ent = str(cand.get("entity", "entity"))

                if is_valid_llm:
                    title = render(ins.get('title', f"Insight on {dim}"), cand)
                    finding = render(ins.get('finding', f"Significant pattern observed in {ent}."), cand)
                    impact = render(ins.get('impact', f"{cand.get('sample_size', 0)} records evaluated"), cand)
                    rec = render(ins.get('recommendation', "Monitor and optimize current strategy."), cand)
                    cat = ins.get("category", "Trend")
                else:
                    # Deterministic Fallback Narrative Generator
                    if c_type == "concentration":
                        title = f"High Concentration in {dim}: {ent}"
                        finding = f"{ent} accounts for {cand.get('share_pct', 0)}% of total {dim} volume across {cand.get('sample_size', 0):,} records."
                        impact = f"{cand.get('share_pct', 0)}% total share ({cand.get('sample_size', 0):,} records)"
                        rec = f"Diversify focus across other {dim} entities to balance distribution risk."
                        cat = "Risk" if cand.get('share_pct', 0) > 30 else "Opportunity"
                    elif c_type == "trend":
                        title = f"MoM Trend Shift in {dim}"
                        finding = f"{dim} registered a {cand.get('mom_pct', 0)}% Month-over-Month change for period {cand.get('period', '')}."
                        impact = f"{cand.get('mom_pct', 0)}% MoM movement"
                        rec = "Track underlying drivers to maintain volume growth and prevent steep drops."
                        cat = "Trend"
                    elif c_type == "failure_rate":
                        title = f"Elevated Failure Rate in {dim}"
                        finding = f"Unhealthy transaction status rate reached {cand.get('rate_pct', 0)}% affecting {cand.get('sample_size', 0):,} records."
                        impact = f"{cand.get('sample_size', 0):,} failed records"
                        rec = "Investigate system log errors and streamline transaction validation flow."
                        cat = "Anomaly"
                    elif c_type == "concentration_risk_overlap":
                        title = f"Top {dim} Also Drives Elevated Risk: {ent}"
                        finding = (
                            f"{ent} accounts for {cand.get('share_pct', 0)}% of total {dim} volume, "
                            f"and its own failure rate is {cand.get('entity_failure_pct', 0)}% "
                            f"versus {cand.get('dataset_failure_pct', 0)}% dataset-wide "
                            f"across {cand.get('sample_size', 0):,} records."
                        )
                        impact = f"{cand.get('entity_failure_pct', 0)}% failure rate within {ent} ({cand.get('sample_size', 0):,} records)"
                        rec = f"Prioritize quality control specifically for {ent} — it is both your largest {dim} segment and disproportionately failure-prone."
                        cat = "Risk"
                    elif c_type == "missing_data":
                        title = f"Data Quality Issue in {dim}"
                        finding = f"Field '{dim}' has {cand.get('rate_pct', 0)}% missing values ({cand.get('sample_size', 0):,} rows)."
                        impact = f"{cand.get('sample_size', 0):,} missing entries"
                        rec = "Enforce required validation rules at data ingestion stage."
                        cat = "Operational"
                    elif c_type == "metric_summary":
                        title = f"Primary Metric Overview: {dim}"
                        finding = f"Total sum for {dim} reached {cand.get('value', 0):,.2f} with average of {cand.get('mean_val', 0):,.2f} per record."
                        impact = f"{cand.get('sample_size', 0):,} total transactions evaluated"
                        rec = "Establish baseline thresholds and set up recurring KPI reporting."
                        cat = "Operational"
                    else:
                        title = f"Dataset Volume Scale Analysis"
                        finding = f"The dataset contains {cand.get('value', 0):,} active records available for analytical processing."
                        impact = f"{cand.get('sample_size', 0):,} active records"
                        rec = "Maintain periodic data refreshes to keep analytical models up to date."
                        cat = "Operational"

                # Category is assigned deterministically from the candidate's
                # analytical type, not left to the LLM's free choice - two
                # different findings (e.g. metric_summary and concentration)
                # could otherwise both land on the same category label even
                # though the dimension-bucket selection above already keeps
                # their underlying analysis distinct, undermining the visible
                # diversity CLAUDE.md's recommendation rule asks for.
                if c_type == "concentration":
                    cat = "Risk" if cand.get('share_pct', 0) > 30 else "Opportunity"
                elif c_type == "concentration_risk_overlap":
                    cat = "Risk"
                elif c_type == "trend":
                    cat = "Trend"
                elif c_type == "failure_rate":
                    cat = "Anomaly"
                else:
                    cat = "Operational"

                try:
                    impact_numeric = float(cand.get("sample_size") or cand.get("value") or cand.get("score") or 0.0)
                except (TypeError, ValueError):
                    impact_numeric = float(cand.get("score", 0.0))

                # Confidence tracks the strength of the underlying deterministic signal
                # (SCORES lambdas above are scaled 0-10), not a flat constant.
                confidence = round(min(0.99, max(0.05, cand.get("score", 0) / 10.0)), 2)

                final_ins = {
                    "id": f"ins_{uuid.uuid4().hex[:8]}",
                    "user_id": user_id,
                    "dataset_id": dataset_id,
                    "title": title,
                    "description": finding,
                    "category": cat,
                    "insight_level": "Operational",
                    "confidence": confidence,
                    "impact": impact,
                    "recommendation": rec,
                    "verified": 1 if is_valid_llm else 0,
                    "audit_sql": f"Deterministic Pandas Pipeline: {c_type}",
                    "score": cand.get("score", 0),
                    "dimension_type": dim,
                    "created_at": datetime.utcnow().isoformat() + "Z"
                }
                final_insights.append(final_ins)

            # Safe DB replacement: Only clear old insights if we have generated new ones!
            if final_insights:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("DELETE FROM insights WHERE user_id = %s AND dataset_id = %s", (user_id, dataset_id))
                    for final_ins in final_insights:
                        try:
                            impact_numeric = float(final_ins.get("score", 0.0))
                        except (TypeError, ValueError):
                            impact_numeric = 0.0
                            
                        cursor.execute('''
                            INSERT INTO insights (id, user_id, dataset_id, title, description, category, insight_level, confidence, impact, recommendation, verified, audit_sql, score, dimension_type, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (
                            final_ins["id"], final_ins["user_id"], final_ins["dataset_id"],
                            final_ins["title"], final_ins["description"], final_ins["category"],
                            final_ins["insight_level"], final_ins["confidence"], impact_numeric,
                            final_ins["recommendation"], final_ins["verified"], final_ins["audit_sql"],
                            final_ins["score"], final_ins["dimension_type"], final_ins["created_at"]
                        ))
                    conn.commit()
                except Exception as db_err:
                    logging.error(f"Failed to commit fresh insights to database: {db_err}")
                finally:
                    conn.close()

            logging.info(f"Successfully generated {len(final_insights)} insights.")
            return final_insights
            
        except Exception as e:
            logging.error(f"DeepInsightsEngine failed: {e}")
            logging.error(traceback.format_exc())
            return []
