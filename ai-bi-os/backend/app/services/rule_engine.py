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

    from app.services.stats_service import find_column, to_datetime_safe, is_non_additive

    # A balance, price, or rate is a level, not a flow: summing it across rows
    # or across a month produces a number with no meaning. Everywhere else in
    # the app (KPIs, forecast, metrics explorer, insights) already defers to
    # this same check, so a rule on "Balance" agrees with what the rest of the
    # product reports for it instead of contradicting it.
    monthly_agg = "mean" if is_non_additive(metric) else "sum"

    if window.lower() == "mom":
        date_col = find_column(df, r"date|month|year|time")
        if not date_col:
            return "ERROR (No Date Column)", None

        df_temp = df.copy()
        df_temp[date_col] = to_datetime_safe(df_temp[date_col])
        df_temp = df_temp.dropna(subset=[date_col])
        if df_temp.empty:
            return "PENDING (Insufficient Data)", None

        monthly = getattr(df_temp.groupby(df_temp[date_col].dt.to_period("M"))[metric], monthly_agg)()
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

    # "latest" is presented to the user as "Latest Value" -- the metric's most
    # recent single reading. Summing the entire column here was a second,
    # independent bug on top of the additive/non-additive one: it evaluated
    # every "Latest Value" rule against a full-history total instead of one
    # row, for every metric, on every dataset. Sort by date (when a date
    # column exists) and read the last row; otherwise fall back to the last
    # row in file order, which is the best available notion of "latest"
    # without one.
    clean_col = df[metric].dropna()
    if clean_col.empty:
        return "PENDING (Insufficient Data)", None
    date_col = find_column(df, r"date|month|year|time")
    if date_col:
        df_temp = df[[date_col, metric]].copy()
        df_temp[date_col] = to_datetime_safe(df_temp[date_col])
        df_temp = df_temp.dropna(subset=[date_col, metric])
        if df_temp.empty:
            return "PENDING (Insufficient Data)", None
        val = float(df_temp.sort_values(date_col).iloc[-1][metric])
    else:
        val = float(clean_col.iloc[-1])
    status = "TRIGGERED" if _check(val, cond, threshold) else "OK"
    return status, _sanitize(val)


def get_metric_series(user_id: str, dataset_id: str, metric: Optional[str], periods: int = 6) -> list:
    """Last `periods` months of `metric`'s aggregated value, for a rule card's
    sparkline. Returns [] whenever a real trend can't be computed (no metric,
    no date column, no data) — never fabricated placeholder points."""
    from app.services.data_processing import get_dataframe
    # to_datetime_safe was missing from this import while still being called
    # below -- a pre-existing NameError. The frontend only fetches this
    # endpoint for MoM-window rules (gated by `enabled: isMoM`), so a rule on
    # any other window never hit it, but GET /rules/{id}/series 500'd for
    # every MoM rule.
    from app.services.stats_service import find_column, to_datetime_safe, is_non_additive

    # A sweep over many rules must not die on one unreadable dataset.
    df = get_dataframe(dataset_id, user_id, raise_if_missing=False)
    if df is None or not metric or metric not in df.columns or not pd.api.types.is_numeric_dtype(df[metric]):
        return []

    date_col = find_column(df, r"date|month|year|time")
    if not date_col:
        return []

    df_temp = df.copy()
    df_temp[date_col] = to_datetime_safe(df_temp[date_col])
    df_temp = df_temp.dropna(subset=[date_col])
    if df_temp.empty:
        return []

    # Same reasoning as evaluate_rule_condition: a level metric's monthly
    # trend is its average, not a monthly total that has no meaning.
    grouped = df_temp.groupby(df_temp[date_col].dt.to_period("M"))[metric]
    monthly = grouped.mean() if is_non_additive(metric) else grouped.sum()
    sorted_periods = sorted(monthly.index)[-periods:]
    return [{"period": str(p), "value": _sanitize(float(monthly[p]))} for p in sorted_periods]


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

    # Each rule already records its own "ERROR (No Data)" status below, which
    # is a truthful result for the run - better than aborting the whole sweep.
    df = get_dataframe(dataset_id, user_id, raise_if_missing=False)
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
