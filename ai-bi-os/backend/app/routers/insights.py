import pandas as pd
from app.services.stats_service import to_datetime_safe
import numpy as np
import re
import os
import json
import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends
from app.services.data_processing import get_active_dataset, get_dataframe
from app.core.security import get_current_user
from app.services.query.duckdb_engine import DuckDBEngine
from app.services.data_processing import get_dataset_path
from app.services.insights_engine import DeepInsightsEngine
from app.core.database import get_db_connection
from litellm import completion
from app.core.config import DB_PATH, LLM_MODEL

router = APIRouter()

def find_column(df: pd.DataFrame, pattern: str, numeric_only: bool = False) -> str:
    cols_to_check = df.select_dtypes(include=[np.number]).columns if numeric_only else df.columns
    for col in cols_to_check:
        if re.search(pattern, col, re.IGNORECASE):
            return col
    return None

def _read_cached_summary(user_id: str, dataset_id: str):
    """The stored summary for this dataset, or None if there isn't one.

    Never raises: a cache that cannot be read must fall through to computing
    the answer, not turn a working dashboard into an error.
    """
    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT summary, verified, facts FROM executive_summaries WHERE user_id = %s AND dataset_id = %s",
                (user_id, dataset_id),
            )
            row = cursor.fetchone()
        finally:
            conn.close()

        if not row:
            return None

        facts = row[2]
        if isinstance(facts, str):
            facts = json.loads(facts)
        return {"summary": row[0], "verified": bool(row[1]), "facts": facts or {}}
    except Exception as exc:
        logging.warning("Could not read the cached executive summary: %s", exc)
        return None


def _cache_summary(user_id: str, dataset_id: str, payload: dict) -> dict:
    """Store a summary and hand the same payload straight back to the caller.

    Returns its argument so it can wrap a `return` without changing what the
    endpoint answers - a failure to cache costs the next visitor some latency,
    never this visitor their result.
    """
    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO executive_summaries (user_id, dataset_id, summary, verified, facts)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, dataset_id)
                DO UPDATE SET summary = EXCLUDED.summary,
                              verified = EXCLUDED.verified,
                              facts = EXCLUDED.facts,
                              created_at = now()
                """,
                (user_id, dataset_id, payload.get("summary", ""),
                 bool(payload.get("verified")), json.dumps(payload.get("facts") or {})),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:
        logging.warning("Could not cache the executive summary: %s", exc)
    return payload


@router.get("/executive-summary")
async def get_executive_summary(current_user: dict = Depends(get_current_user)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        return {"summary": "AI features are not configured - add GROQ_API_KEY to your .env file.", "verified": False}
        
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"summary": "No dataset uploaded yet. Upload a dataset to see AI insights.", "verified": False}

    # A dataset's id is minted fresh for every upload and every new version, so
    # its contents never change under a given id. That makes the summary
    # cacheable outright: same id, same facts, same sentences. Worth doing
    # because this endpoint sits on the dashboard's critical path and used to
    # make a blocking LLM call on every single load - including every time the
    # user navigated back to the dashboard.
    cached = _read_cached_summary(current_user["id"], dataset_info["id"])
    if cached is not None:
        return cached

    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        return {"summary": "Failed to load data.", "verified": False}

    # Compute deterministic facts
    row_count = len(df)

    # ── INR currency formatter ─────────────────────────────────────────────
    def format_inr(val: float) -> str:
        """Format a value in Indian number system (Cr / L / K). Abbreviates
        by magnitude regardless of sign, so a negative total (e.g. a net
        refund/loss figure) gets "-\u20b93.40L" instead of the raw
        "\u20b9-3,400,718.52" the old sign-blind >= checks fell through to."""
        sign = "-" if val < 0 else ""
        abs_val = abs(val)
        if abs_val >= 1_00_00_000:
            return f"{sign}\u20b9{abs_val / 1_00_00_000:.2f}Cr"
        if abs_val >= 1_00_000:
            return f"{sign}\u20b9{abs_val / 1_00_000:.2f}L"
        if abs_val >= 1_000:
            return f"{sign}\u20b9{abs_val / 1_000:.2f}K"
        return f"{sign}\u20b9{abs_val:,.2f}"

    rev_col = find_column(df, r'revenue|sales|amount|\bmrr\b|\barr\b|turnover|income|earnings|\bgmv\b|sales_amount|order_value|net_revenue|total_revenue', numeric_only=True)
    date_col = find_column(df, r'date|month|year|time')

    # Detect row label from semantic dict (use 'transactions' for UPI/payment domains)
    semantic_dict = dataset_info.get("semantic_dict", {}) or {}
    domain = semantic_dict.get("domain", "generic").lower()
    row_label = "transactions" if any(x in domain for x in ["upi", "payment", "finance", "banking", "transaction"]) else "records"

    facts = {
        "dataset_name": dataset_info["name"],
        "row_count": row_count,
        "row_label": row_label,
    }

    if rev_col and pd.api.types.is_numeric_dtype(df[rev_col]):
        total_value = float(df[rev_col].sum())
        facts["total_value"] = total_value
        facts["metric_name"] = rev_col
        facts["formatted_total"] = format_inr(total_value)

        if date_col:
            try:
                df[date_col] = to_datetime_safe(df[date_col])
                df_clean = df.dropna(subset=[date_col])
                if not df_clean.empty:
                    periods = df_clean.groupby(df_clean[date_col].dt.to_period('M'))
                    if len(periods) >= 2:
                        sorted_periods = sorted(periods.groups.keys())
                        recent = float(periods.get_group(sorted_periods[-1])[rev_col].sum())
                        prior = float(periods.get_group(sorted_periods[-2])[rev_col].sum())
                        if prior > 0:
                            pct_change = ((recent - prior) / prior) * 100
                            facts["percent_change"] = round(pct_change, 1)
            except Exception:
                pass

    # Prepare LLM Prompt
    prompt = (
        f"Write a concise 2-3 sentence executive summary based ONLY on these facts: {facts}.\n"
        "Rules:\n"
        "- Do NOT use the raw file name (like dataset.csv). Refer to it as 'The uploaded dataset' or 'The uploaded banking transaction dataset'.\n"
        "- Use \u20b9 (rupee symbol) for currency values in Indian format (e.g. \u20b98.62Cr, \u20b945.2L). NEVER use $ or £.\n"
        "- Use the word 'transactions' instead of 'data points', 'rows', or 'records'.\n"
        "- Use the phrase 'Transaction Value' instead of 'Amount' or 'Total Amount'.\n"
        "- Add comma separators for numbers above 1,000 (e.g. 5,200 not 5200).\n"
        "- Do NOT invent, estimate, or round numbers beyond what the facts contain."
    )
    
    try:
        response = completion(
            model=LLM_MODEL, 
            messages=[{"role": "user", "content": prompt}],
            api_key=os.getenv("GROQ_API_KEY")
        )
        llm_summary = response.choices[0].message.content.strip()
        llm_summary = llm_summary.replace('$', '\u20b9').replace('records', 'transactions').replace('Amount', 'Transaction Value').replace('amount', 'Transaction Value')
        
        # Verify numbers
        import string
        def extract_numbers(text):
            return re.findall(r'-?\d+\.?\d*', text.replace(',', ''))
            
        llm_nums = extract_numbers(llm_summary)
        fact_str = str(facts)
        fact_nums = extract_numbers(fact_str)
        
        verified = True
        for num in llm_nums:
            # allow some flexibility for rounding
            found = False
            try:
                num_float = float(num)
                for f_num in fact_nums:
                    if abs(float(f_num) - num_float) < 1.0: # Close enough
                        found = True
                        break
            except Exception:
                pass
            if not found:
                verified = False
                break
                
        if verified:
            return _cache_summary(current_user["id"], dataset_info["id"],
                                  {"summary": llm_summary, "verified": True, "facts": facts})
        else:
            raise Exception("Hallucination detected")
            
    except Exception as e:
        # Fallback to deterministic template (no LLM)
        dataset_name = dataset_info['name']
        count_str = f"{row_count:,}"  # always comma-separated

        if "total_value" in facts and "metric_name" in facts:
            metric_name = "Transaction Value" if "amount" in facts['metric_name'].lower() else facts['metric_name']
            formatted_total = facts.get("formatted_total") or format_inr(facts['total_value'])

            if "percent_change" in facts:
                pct = facts["percent_change"]
                direction = "increase" if pct > 0 else "decrease"
                summary = (
                    f"The uploaded dataset shows total {metric_name} of {formatted_total} "
                    f"across {count_str} transactions, "
                    f"a {abs(pct):.1f}% {direction} versus the prior period."
                )
            else:
                summary = (
                    f"The uploaded dataset shows total {metric_name} of {formatted_total} "
                    f"across {count_str} transactions."
                )
        else:
            summary = f"The uploaded dataset contains {count_str} {row_label}."

        # The deterministic fallback is cached too. It is reached when the LLM
        # is unavailable or contradicted the facts, and in both cases the same
        # input would produce the same fallback - there is nothing to gain from
        # calling out again on the next load just to fail again.
        return _cache_summary(current_user["id"], dataset_info["id"],
                              {"summary": summary, "verified": True, "facts": facts})

@router.post("/deep-analyze")
async def deep_analyze(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"success": False, "message": "No active dataset."}
        
    db_engine = DuckDBEngine()
    file_path = get_dataset_path(dataset_info["filepath"])
    format_type = "parquet" if file_path.endswith(".parquet") else "csv"
    db_engine.register_dataset("active_dataset", file_path, format=format_type)
    
    engine = DeepInsightsEngine(db_engine)
    insights = engine.generate_insights(current_user["id"], dataset_info["id"])
    db_engine.close()
    return {"success": True, "insights": insights}

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
    if val >= 1_000_000_000:
        return f"{prefix}{val / 1_000_000_000:.2f}B {label}"
    elif val >= 1_000_000:
        return f"{prefix}{val / 1_000_000:.2f}M {label}"
    elif val >= 1_000:
        return f"{prefix}{val / 1_000:.1f}K {label}"
    else:
        if isinstance(val, (int, float)) and float(val).is_integer():
            return f"{prefix}{int(val):,} {label}"
        else:
            return f"{prefix}{val:,.2f} {label}"


def format_insight_impact(impact_val, title: str, dimension_type=None) -> str:
    """Turns a stored insight's raw `impact` into the display string shown on
    both the private Insights page and the public share page. Pulled out to
    one place after the share page's own copy of this logic reintroduced a
    bug already fixed here: it fed the raw number straight to a client-side
    formatter that defaults to currency, so a shared dashboard showed
    "1.4K Records" privately but "₹1.4K Avg" on the public link for the
    exact same insight -- the two paths disagreed about the same number.
    """
    if impact_val is None:
        return impact_val
    try:
        impact_str = str(impact_val).strip()
        numeric_part = re.findall(r'[0-9]+(?:\.[0-9]+)?', impact_str.replace(',', ''))
        if not (numeric_part and len(numeric_part[0]) == len(impact_str.replace('₹', '').replace('$', '').replace('£', '').strip())):
            return replace_revenue_terminology(reformat_currency(impact_str))
        f_val = float(numeric_part[0])
        # Insights from the deterministic engine store a row count in
        # `impact` (they are the only ones that set dimension_type). Counting
        # rows is not money, so a title-keyword guess alone stamped a
        # currency symbol on them.
        from_engine = dimension_type is not None
        if from_engine:
            is_curr = False
        else:
            is_curr = (
                any(sym in impact_str for sym in ('₹', '$', '£'))
                or not any(x in title.lower() for x in ["count", "volume", "transactions"])
            )
        label = "Average" if "avg" in title.lower() else ("Records" if not is_curr else "Processed")
        return format_impact_value(f_val, is_curr, label)
    except Exception:
        return impact_val

@router.get("")
async def list_insights(dataset_version_id: str = None, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []
        
    # Check DB first
    conn = get_db_connection()
    conn.row_factory = None
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM insights 
        WHERE user_id = %s AND dataset_id = %s 
        ORDER BY verified DESC, created_at DESC
    ''', (current_user["id"], dataset_info["id"]))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        result_list = []
        for r in rows:
            d = dict(r)
            # Re-format on-the-fly to guarantee cached old data gets updated correctly in UI
            d['title'] = replace_revenue_terminology(reformat_currency(d.get('title', '')))
            d['description'] = replace_revenue_terminology(reformat_currency(d.get('description', '')))
            
            # Format impact value if it is a numeric float
            d['impact'] = format_insight_impact(d.get('impact'), d.get('title', ''), d.get('dimension_type'))
                
            d['recommendation'] = replace_revenue_terminology(reformat_currency(d.get('recommendation', '')))
            
            created_at = d.get('created_at')
            if created_at and not created_at.endswith('Z'):
                d['created_at'] = created_at.replace(' ', 'T') + 'Z'
                
            result_list.append(d)
        return result_list
        
    # Fallback to Z-Score Anomalies
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        return []

    date_col = find_column(df, r'date|month|year|time')
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    anomalies = []

    if date_col and len(numeric_cols) > 0:
        try:
            df[date_col] = to_datetime_safe(df[date_col])
            df_clean = df.dropna(subset=[date_col])
            
            # Group by month
            monthly_data = df_clean.groupby(df_clean[date_col].dt.to_period('M'))[numeric_cols].sum()
            
            if len(monthly_data) >= 3: # Need some history
                for col in numeric_cols:
                    series = monthly_data[col]
                    mean = series.mean()
                    std = series.std()
                    
                    if std > 0:
                        recent_val = series.iloc[-1]
                        z_score = (recent_val - mean) / std
                        
                        if abs(z_score) > 1.5:
                            is_drop = z_score < 0
                            category = "Risk" if is_drop else "Opportunity"
                            title = f"Significant {'Drop' if is_drop else 'Spike'} in {col}"
                            desc = f"{col} was {recent_val:.2f} in the most recent period, which is {abs(z_score):.1f} standard deviations from the mean."
                            impact = float(abs(recent_val))

                            # Context-aware recommendation based on direction
                            if is_drop:
                                rec = (
                                    f"Monitor the trend of {col} closely. "
                                    "Analyze user segments and operational patterns to identify and mitigate "
                                    "factors contributing to this decline."
                                )
                            else:
                                rec = (
                                    f"Analyze the driving factors behind the growth in {col}. "
                                    "Leverage this spike to optimize scheduling, marketing, or resource allocation "
                                    "for future cycles."
                                )

                            is_curr = not any(x in col.lower() for x in ["count", "volume", "sample_size", "transactions"])
                            label = "Average" if "avg" in col.lower() or "mean" in col.lower() else ("Transactions" if not is_curr else "Processed")
                            formatted_impact = format_impact_value(impact, is_curr, label)

                            formatted_title = replace_revenue_terminology(reformat_currency(title))
                            formatted_desc = replace_revenue_terminology(reformat_currency(desc))
                            formatted_rec = replace_revenue_terminology(reformat_currency(rec))

                            anomalies.append({
                                "id": f"ins_{uuid.uuid4().hex[:8]}",
                                "title": formatted_title,
                                "description": formatted_desc,
                                "category": category,
                                "confidence": round(min(0.99, abs(z_score) / 3), 2),
                                "impact": formatted_impact,        # display string
                                "_impact_raw": impact,             # raw float for DB
                                "recommendation": formatted_rec,
                                "verified": 1,
                                "created_at": datetime.utcnow().isoformat() + "Z"
                            })
        except Exception:
            pass

    if anomalies:
        conn = get_db_connection()
        cursor = conn.cursor()
        for a in anomalies:
            cursor.execute('''
                INSERT INTO insights (id, user_id, dataset_id, title, description, category, insight_level, confidence, impact, recommendation, verified, audit_sql, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                a["id"],
                current_user["id"],
                dataset_info["id"],
                a["title"],
                a["description"],
                a["category"],
                "Operational",
                a["confidence"],
                a["_impact_raw"],   # store raw float, not formatted string
                a["recommendation"],
                a["verified"],
                "Computed via Pandas Z-Score Z=(X-μ)/σ",
                a["created_at"]
            ))
        conn.commit()
        conn.close()

    # Return display-friendly list (with formatted impact string)
    return anomalies
