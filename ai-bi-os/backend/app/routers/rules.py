import os
import json
import re
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Body
from app.core.database import get_db_connection
from app.services.data_processing import get_active_dataset, get_dataframe
from app.services.rule_engine import evaluate_and_persist_rules, get_metric_series
from app.core.security import get_current_user
from app.core.config import LLM_MODEL
from litellm import completion

router = APIRouter()


@router.get("")
async def get_rules(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []
    return evaluate_and_persist_rules(current_user["id"], dataset_info["id"])


@router.post("/evaluate")
async def evaluate_rules_now(current_user: dict = Depends(get_current_user)):
    """Manual "Run checks now" trigger — same detection path as GET, just
    invoked explicitly instead of as a side effect of loading the page."""
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []
    return evaluate_and_persist_rules(current_user["id"], dataset_info["id"])


@router.get("/{rule_id}/history")
async def get_rule_history(rule_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM rules WHERE id = %s AND user_id = %s', (rule_id, current_user["id"]))
    if not cursor.fetchone():
        conn.close()
        return []
    cursor.execute(
        'SELECT * FROM rule_events WHERE rule_id = %s ORDER BY created_at DESC LIMIT 50',
        (rule_id,),
    )
    events = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return events


@router.get("/{rule_id}/series")
async def get_rule_series(rule_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rules WHERE id = %s AND user_id = %s', (rule_id, current_user["id"]))
    rule = cursor.fetchone()
    conn.close()
    if not rule:
        return []
    rule = dict(rule)
    return get_metric_series(current_user["id"], rule["dataset_id"], rule.get("metric_column"))


@router.post("")
async def create_rule(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"error": "No dataset"}

    rule_id = f"rule_{uuid.uuid4().hex[:8]}"
    created_at = datetime.utcnow().isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO rules (id, user_id, dataset_id, name, metric_column, condition, threshold, "window", is_active, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        rule_id, current_user["id"], dataset_info["id"],
        data.get("name", "New Rule"),
        data.get("metric_column", ""),
        data.get("condition", ">"),
        float(data.get("threshold", 0)),
        data.get("window", "latest"),
        1, created_at
    ))
    conn.commit()
    conn.close()
    return {"id": rule_id, "success": True}


@router.patch("/{rule_id}")
async def update_rule(rule_id: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current rule
    cursor.execute('SELECT * FROM rules WHERE id = %s AND user_id = %s', (rule_id, current_user["id"]))
    rule = cursor.fetchone()
    if not rule:
        conn.close()
        return {"error": "Rule not found or unauthorized"}

    # Build update query dynamically based on provided fields
    update_fields = []
    params = []

    if "is_active" in data:
        update_fields.append("is_active = %s")
        params.append(1 if data["is_active"] else 0)
    if "name" in data:
        update_fields.append("name = %s")
        params.append(data["name"])
    if "metric_column" in data:
        update_fields.append("metric_column = %s")
        params.append(data["metric_column"])
    if "condition" in data:
        update_fields.append("condition = %s")
        params.append(data["condition"])
    if "threshold" in data:
        update_fields.append("threshold = %s")
        params.append(float(data["threshold"]))
    if "window" in data:
        update_fields.append('"window" = %s')
        params.append(data["window"])

    if update_fields:
        query = f"UPDATE rules SET {', '.join(update_fields)} WHERE id = %s AND user_id = %s"
        params.extend([rule_id, current_user["id"]])
        cursor.execute(query, tuple(params))
        conn.commit()

    conn.close()
    return {"success": True}


@router.delete("/{rule_id}")
async def delete_rule(rule_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    # rule_events has a FK on rule_id — must go first.
    cursor.execute('DELETE FROM rule_events WHERE rule_id = %s AND user_id = %s', (rule_id, current_user["id"]))
    cursor.execute('DELETE FROM rules WHERE id = %s AND user_id = %s', (rule_id, current_user["id"]))
    conn.commit()
    conn.close()
    return {"success": True}


@router.post("/parse-text")
async def parse_text_rule(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        return {"error": "AI features are not configured - add GROQ_API_KEY to your .env file."}

    text = data.get("text", "")
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"error": "No dataset"}

    df = get_dataframe(dataset_info["id"], current_user["id"])
    cols = df.columns.tolist() if df is not None else []

    prompt = f"""Given the following dataset columns: {cols}
Parse the user's natural language business rule into a JSON object.
Rule text: "{text}"
Return a valid JSON object with:
- name (string, a short title for the rule)
- metric_column (string, MUST be exactly one of the available columns)
- condition (string, one of: ">", "<", ">=", "<=", "==", "pct_change_gt", "pct_change_lt", "gt", "lt")
- threshold (number)
- window (string, either "MoM" or "latest")"""

    try:
        res = completion(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            api_key=os.getenv("GROQ_API_KEY")
        )
        content = res.choices[0].message.content
        m = re.search(r'\{.*\}', content, re.DOTALL)
        if m:
            content = m.group(0)
        parsed = json.loads(content)
        return {"success": True, "parsed": parsed}
    except Exception as e:
        return {"success": False, "error": str(e)}
