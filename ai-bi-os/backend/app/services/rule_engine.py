"""Business rule detection: evaluates a rule's condition against live data,
persists the result on the rule row, and — on a fresh transition into
TRIGGERED — writes an audit event plus an in-app notification. This is the
single source of truth for rule evaluation; both the on-demand GET /rules
read path and the upload-triggered/manual-evaluate write paths call into it
so status can never drift between them.
"""
import math
import uuid
from datetime import datetime
from typing import Optional, Tuple

import pandas as pd

from app.core.database import get_db_connection

_COND_ALIASES = {"gt": ">", "lt": "<", "pct_change_gt": ">", "pct_change_lt": "<", "eq": "=="}


def _sanitize(value):
    """NaN/Infinity aren't valid JSON — collapse them to None rather than
    letting FastAPI's encoder raise on an otherwise-successful evaluation."""
    if value is None:
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return value


def _check(value: float, cond: str, threshold: float) -> bool:
    if cond == ">":
        return value > threshold
    if cond == "<":
        return value < threshold
    if cond == ">=":
        return value >= threshold
    if cond == "<=":
        return value <= threshold
    if cond == "==":
        return value == threshold
    return False


def evaluate_rule_condition(df: pd.DataFrame, rule: dict) -> Tuple[str, Optional[float]]:
    """Returns (status, current_value) for a single rule against `df`.

    Statuses: INACTIVE, ERROR (Invalid Metric), ERROR (No Date Column),
    ERROR (Invalid Baseline), PENDING (Insufficient Data), OK, TRIGGERED.
    The ERROR/PENDING split matters for accuracy: a rule that can't be
    evaluated yet (e.g. only one month of data for a MoM rule) should never
    read as "OK", which implies it was checked and passed.
    """
    if not rule.get("is_active"):
        return "INACTIVE", None

    metric = rule.get("metric_column")
    if not metric or metric not in df.columns or not pd.api.types.is_numeric_dtype(df[metric]):
        return "ERROR (Invalid Metric)", None

    raw_cond = (rule.get("condition") or ">").lower()
    cond = _COND_ALIASES.get(raw_cond, rule.get("condition") or ">")
    threshold = float(rule.get("threshold") or 0)
    window = rule.get("window") or "latest"

    if window.lower() == "mom":
        from app.services.stats_service import find_column

        date_col = find_column(df, r"date|month|year|time")
        if not date_col:
            return "ERROR (No Date Column)", None

        df_temp = df.copy()
        df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors="coerce")
        df_temp = df_temp.dropna(subset=[date_col])
        if df_temp.empty:
            return "PENDING (Insufficient Data)", None

        monthly = df_temp.groupby(df_temp[date_col].dt.to_period("M"))[metric].sum()
        if len(monthly) < 2:
            return "PENDING (Insufficient Data)", None

        sorted_periods = sorted(monthly.index)
        recent = float(monthly[sorted_periods[-1]])
        prior = float(monthly[sorted_periods[-2]])
        if prior == 0:
            return "ERROR (Invalid Baseline)", None

        pct_change = ((recent - prior) / prior) * 100
        status = "TRIGGERED" if _check(pct_change, cond, threshold) else "OK"
        return status, _sanitize(pct_change)

    val = float(df[metric].sum())
    status = "TRIGGERED" if _check(val, cond, threshold) else "OK"
    return status, _sanitize(val)


def evaluate_and_persist_rules(user_id: str, dataset_id: str) -> list[dict]:
    """Evaluates every rule the user has against `dataset_id`, persists the
    result, and delivers a notification for each fresh TRIGGERED transition.
    Returns the rules with live status/current_value merged in — the exact
    shape the frontend already expects from GET /rules.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM rules WHERE user_id = %s AND dataset_id = %s ORDER BY created_at DESC',
        (user_id, dataset_id),
    )
    rules = [dict(r) for r in cursor.fetchall()]
    if not rules:
        conn.close()
        return []

    from app.services.data_processing import get_dataframe

    df = get_dataframe(dataset_id, user_id)
    now = datetime.utcnow().isoformat()

    for rule in rules:
        if df is None:
            status, value = "ERROR (No Data)", None
        else:
            status, value = evaluate_rule_condition(df, rule)

        prev_status = rule.get("last_status")
        newly_triggered = status == "TRIGGERED" and prev_status != "TRIGGERED"

        last_triggered_at = rule.get("last_triggered_at")
        if status == "TRIGGERED":
            last_triggered_at = now

        cursor.execute(
            'UPDATE rules SET last_status = %s, last_value = %s, last_evaluated_at = %s, last_triggered_at = %s WHERE id = %s',
            (status, value, now, last_triggered_at, rule["id"]),
        )

        if newly_triggered:
            message = (
                f'"{rule.get("name")}" triggered — {rule.get("metric_column")} '
                f'{rule.get("condition")} {rule.get("threshold")} '
                f'(current: {value if value is not None else "n/a"})'
            )
            cursor.execute(
                '''INSERT INTO rule_events
                   (id, rule_id, user_id, dataset_id, status, current_value, threshold, condition, message, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (
                    f"revt_{uuid.uuid4().hex[:10]}", rule["id"], user_id, dataset_id,
                    status, value, rule.get("threshold"), rule.get("condition"), message, now,
                ),
            )
            cursor.execute(
                '''INSERT INTO notifications
                   (id, user_id, type, title, message, rule_id, is_read, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, 0, %s)''',
                (
                    f"notif_{uuid.uuid4().hex[:10]}", user_id, "rule_triggered",
                    f'Rule triggered: {rule.get("name")}', message, rule["id"], now,
                ),
            )

        rule["status"] = status
        rule["current_value"] = value
        rule["last_status"] = status
        rule["last_value"] = value
        rule["last_evaluated_at"] = now
        rule["last_triggered_at"] = last_triggered_at

    conn.commit()
    conn.close()
    return rules
