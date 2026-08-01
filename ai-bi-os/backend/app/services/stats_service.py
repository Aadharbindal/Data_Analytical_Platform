import pandas as pd
import numpy as np
import re
import warnings
from typing import Optional
from scipy import stats as scipy_stats

# Matches the identifier-detection convention used in semantic_classification.py's
# entity_ids regex. A numeric "entity" column (the thing a KPI counts distinct
# instances of — customer, transaction, reference number...) should be counted
# via nunique(), not summed — summing a column of reference numbers produces a
# meaningless total. The bare `id|code|uuid` substring check this used to be
# missed extremely common reference-number naming like "Ref No" or "Txn Number",
# since those don't contain "id" as a substring.
_ENTITY_ID_PATTERN = re.compile(r'\b(id|key|code|uuid|number|num|phone|zip|postal|ref|reference|utr)\b|_id$|id$|^id', re.IGNORECASE)

# Columns that are NOT additive across rows: rates, percentages, per-unit
# prices, ratings, ages, running balances, stock-on-hand. Adding these up
# produces a number with no meaning — "total discount_pct = 11,920" for a
# column of percentages, or "total rating = 4,467" for 1-5 stars. Averaging
# is the only sensible default for them.
#
# Matched with word boundaries against a name whose separators have been
# normalized to spaces (see is_non_additive), so "discount_pct" -> "discount
# pct" matches `pct` while "package"/"usage" correctly do NOT match `age`.
_NON_ADDITIVE_PATTERN = re.compile(
    r'\b('
    r'rate|ratio|percent|percentage|pct|score|rating|nps|'
    r'avg|average|mean|median|price|margin|share|index|'
    r'utilization|util|probability|prob|age|yield|'
    r'balance|outstanding|headcount|level|onhand|'
    # Per-unit quantities: unit_cost, unit_price, price_per_sqft,
    # revenue_per_user. Adding them across rows produces a number with no
    # meaning. Singular "unit" only, so units_produced / units_sold — which are
    # genuine additive totals — keep summing.
    r'unit|per'
    r')\b',
    re.IGNORECASE,
)


def is_non_additive(column_name) -> bool:
    """True when summing this column across rows would be meaningless."""
    normalized = str(column_name).replace('_', ' ').replace('-', ' ')
    return bool(_NON_ADDITIVE_PATTERN.search(normalized))


# Column names that denote monetary values. Deliberately excludes bare "rate"
# and "count" style words, which are ratios and tallies rather than money.
_MONEY_PATTERN = re.compile(
    r'\b(amount|amt|revenue|sales|price|cost|salary|wage|payroll|spend|spending|'
    r'budget|bill|billing|invoice|payment|paid|debit|credit|balance|deposit|'
    r'withdrawal|fee|fees|charge|charges|profit|margin|income|expense|expenses|'
    r'value|mrr|arr|gmv|turnover|premium|refund|discount.?amount|tax|total.?due)\b',
    re.IGNORECASE,
)


def is_money_like(column_name) -> bool:
    """True when a column's name indicates it holds a monetary value."""
    normalized = str(column_name).replace('_', ' ').replace('-', ' ')
    return bool(_MONEY_PATTERN.search(normalized))


def to_datetime_safe(series):
    """Parse a date column without silently mis-reading day-first dates.

    pandas assumes month-first for slash dates, so a statement written
    "01/04/2024" (1 April, the norm outside the US) is read as 4 January, and
    "30/04/2025" has no 30th month so it becomes NaT and the row silently
    vanishes from every date-based figure. Both failures are invisible: the
    totals still render, they are just attributed to the wrong months and
    computed over fewer rows.

    Parsing both ways and keeping whichever resolves more values decides this
    from the data instead of guessing — genuinely month-first data still wins
    when it is the better fit. Only when the two are indistinguishable (every
    day ≤ 12) does the tie-break matter, and there day-first matches both this
    product's audience and the majority of the world's date formats.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return series

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        month_first = pd.to_datetime(series, errors="coerce")
        day_first = pd.to_datetime(series, errors="coerce", dayfirst=True)

    if int(month_first.notna().sum()) > int(day_first.notna().sum()):
        return month_first
    return day_first


def explain_insufficient_rows(df, columns, min_rows: int = 20) -> str:
    """Explain *why* dropping nulls left too few rows to model on.

    Selecting several columns and dropping incomplete rows can silently
    collapse a large dataset to nothing — most commonly when two columns are
    mutually exclusive by design, as a bank statement's Debit and Credit are
    (every row populates exactly one of them). A bare "not enough data" leaves
    the user with no idea which column caused it or what to pick instead, so
    this reports the per-column coverage and the best workable subset.
    """
    present = [c for c in columns if c in df.columns]
    if not present:
        return f"Not enough data: need at least {min_rows} complete rows."

    total = len(df)
    remaining = len(df[present].dropna())
    counts = {c: int(df[c].notna().sum()) for c in present}
    worst = sorted(counts, key=lambda c: counts[c])

    # Find the largest subset of the chosen columns that still yields enough
    # complete rows, dropping the sparsest columns first.
    usable, trial = None, list(present)
    while len(trial) > 1:
        trial = [c for c in trial if c != worst[0]] if len(trial) == len(present) else trial[:-1]
        trial_sorted = sorted(present, key=lambda c: -counts[c])[:len(trial)]
        if len(df[trial_sorted].dropna()) >= min_rows:
            usable = trial_sorted
            break

    detail = ", ".join(f"'{c}' has {counts[c]} of {total} rows filled" for c in sorted(present, key=lambda c: counts[c]))
    msg = (f"Only {remaining} rows have a value in every selected column, "
           f"but at least {min_rows} are needed. Coverage: {detail}.")

    empty_pairs = [
        (a, b) for i, a in enumerate(present) for b in present[i + 1:]
        if len(df[[a, b]].dropna()) == 0
    ]
    if empty_pairs:
        pairs = "; ".join(f"'{a}' and '{b}'" for a, b in empty_pairs[:3])
        msg += (f" {pairs} are never populated on the same row, "
                f"so they cannot be modelled together.")
    if usable:
        msg += " Try " + ", ".join(f"'{c}'" for c in usable) + " instead."
    return msg


def is_identifier_like(series, column_name, total_rows: int) -> bool:
    """True when a column behaves like a per-row identifier rather than a
    measurement, and so should not be offered as an ML feature or target.

    Cardinality alone is a poor test. A continuous measurement — an amount, a
    running balance, a price — is naturally almost entirely distinct, so a
    "more than half the values are unique, therefore it's an ID" rule discards
    exactly the columns worth modelling.

    Restricting that rule to integer columns was not enough. Measured across ten
    varied datasets it caught no real identifier and eight genuine measures:
    units_produced (91% distinct), stock_qty (96%), impressions (99.6%), clicks,
    conversions, area_sqft, reorder_level, units_sold_last_month. Every one was
    then withheld from regression, classification and clustering — the columns
    those datasets exist to model. The single real numeric identifier in the set,
    "Ref No", was caught by the name pattern above and needed no help.

    So the cardinality fallback now only fires on a strict key: every non-null
    value distinct, with no near-miss tolerance. A count that happens to be 99%
    distinct is a measurement; a column with no repeats at all in a decently
    sized table is behaving like a key. Sparse and tiny columns are left alone
    because uniqueness carries no signal there.
    """
    if _ENTITY_ID_PATTERN.search(str(column_name)):
        return True
    if total_rows <= 0:
        return False
    try:
        if pd.api.types.is_float_dtype(series):
            return False
        if is_money_like(column_name):
            return False
        # Callers pass the column both raw and already dropna()'d, so normalise
        # here rather than depending on which one arrived.
        values = series.dropna()
        n = len(values)
        if n < 20 or n < total_rows * 0.5:
            return False
        return int(values.nunique()) == n
    except Exception:
        return False


def pick_default_metric(df: pd.DataFrame):
    """Choose the numeric column to show when the caller didn't name one.

    Several endpoints used to fall back to the first numeric column, which is
    whatever the CSV happened to lead with. On a bank statement that is the
    reference number, so the Forecast Center and Time Series pages opened on a
    projection of cheque numbers. Skip identifiers, prefer an actual money
    column, and only fall back to the raw first column when every numeric
    column looks like an identifier — never return nothing where the old code
    would have returned something.
    """
    num_cols = list(df.select_dtypes(include=[np.number]).columns)
    if not num_cols:
        return None
    total_rows = len(df)
    candidates = [
        c for c in num_cols
        if not is_identifier_like(df[c].dropna(), c, total_rows)
    ]
    # Order of preference, tested against ten datasets from different domains:
    #   1. an additive money total   — net_revenue, mrr, bill_amount, spend
    #   2. any money column          — price_inr on listings, price on trades,
    #                                  which are per-unit but still the headline
    #   3. an additive non-money total — units_produced, stock_qty
    #   4. whatever is left
    # Putting plain totals above per-unit money (step 3 over step 2) was tried
    # and picked area_sqft over price_inr for real estate, so money wins first.
    for group in (
        [c for c in candidates if is_money_like(c) and not is_non_additive(c)],
        [c for c in candidates if is_money_like(c)],
        [c for c in candidates if not is_non_additive(c)],
        candidates,
    ):
        if group:
            return group[0]
    return num_cols[0]


def find_column(df: pd.DataFrame, pattern: str, numeric_only: bool = False) -> str:
    cols_to_check = df.select_dtypes(include=[np.number]).columns if numeric_only else df.columns
    for col in cols_to_check:
        if re.search(pattern, col, re.IGNORECASE):
            return col
    return None


def robust_outlier_stats(series: pd.Series, z_threshold: float = 3.0, mad_threshold: float = 3.5) -> dict:
    """
    Flags outliers using a method appropriate to the data's shape instead of
    always applying the classic mean/std Z-score. That classic Z-score
    assumes a roughly symmetric distribution — on skewed data it both
    inflates std (masking real outliers) and gets thrown off by the very
    tail it's trying to flag. For |skewness| > 1 this switches to the
    median/MAD-based modified Z-score (Iglewicz & Hoaglin), which is robust
    to skew and to the outliers themselves. The IQR/Tukey-fence count is
    shape-agnostic and always reported alongside for cross-reference.
    """
    clean = series.dropna()
    n = len(clean)
    if n < 2:
        return {"count": 0, "method": "insufficient_data", "skewness": 0.0, "iqr_count": 0}

    try:
        skewness = float(scipy_stats.skew(clean))
        if not np.isfinite(skewness):
            skewness = 0.0
    except Exception:
        skewness = 0.0

    std = float(clean.std())
    if std == 0 or not np.isfinite(std):
        count, method = 0, "zero_variance"
    elif abs(skewness) > 1.0:
        median = clean.median()
        mad = float(np.median(np.abs(clean - median)))
        if mad == 0:
            # Degenerate MAD (e.g. >50% of values identical) — fall back to classic Z-score
            z = np.abs((clean - clean.mean()) / std)
            count = int((z > z_threshold).sum())
            method = "z_score"
        else:
            modified_z = 0.6745 * (clean - median) / mad
            count = int((np.abs(modified_z) > mad_threshold).sum())
            method = "modified_z_score_mad"
    else:
        z = np.abs((clean - clean.mean()) / std)
        count = int((z > z_threshold).sum())
        method = "z_score"

    q1 = clean.quantile(0.25)
    q3 = clean.quantile(0.75)
    iqr = q3 - q1
    iqr_count = int(((clean < (q1 - 1.5 * iqr)) | (clean > (q3 + 1.5 * iqr))).sum())

    return {"count": count, "method": method, "skewness": round(skewness, 2), "iqr_count": iqr_count}

def compute_kpis(df: pd.DataFrame, semantic_dict: dict = None) -> dict:
    if df is None:
        return {"kpis": [], "chart_data": []}
        
    if not semantic_dict:
        # Fallback to local heuristic detection
        from app.services.semantic_classification import fallback_classify
        _, semantic_dict = fallback_classify(df, "Active Dataset")
    else:
        # Always run sanitization dynamically in compute_kpis as a failsafe
        from app.services.semantic_classification import validate_and_sanitize_business_terminology
        domain = semantic_dict.get("domain", "generic")
        bus_term = semantic_dict.get("business_terminology", {})
        validate_and_sanitize_business_terminology(df, domain, bus_term)
        
    # get_dataframe() hands back the shared cached frame, so writing the parsed
    # date column straight onto `df` (below) would mutate that cache in place —
    # every later request, for every other endpoint, would then read a frame
    # whose date column had already been converted. Work on our own copy.
    df = df.copy()
    original_df = df.copy()
    kpis = []
    
    # Extract terms
    bus_term = semantic_dict.get("business_terminology", {})
    sem_dict = semantic_dict.get("semantic_dictionary", {})
    
    primary_metric = bus_term.get("primary_metric")
    primary_label = bus_term.get("primary_metric_label", "Total Value")
    primary_op = bus_term.get("primary_metric_op", "sum")
    primary_type = bus_term.get("primary_metric_type", "currency")
    
    entity_col = bus_term.get("entity_col")
    entity_label = bus_term.get("entity_count_label", "Total Items")
    
    secondary_metric = bus_term.get("secondary_metric")
    secondary_label = bus_term.get("secondary_metric_label", "Average Value")
    secondary_op = bus_term.get("secondary_metric_op", "mean")
    secondary_type = bus_term.get("secondary_metric_type", "generic")
    
    status_col = bus_term.get("status_col")
    status_label = bus_term.get("status_metric_label", "Success Rate")
    status_healthy = bus_term.get("status_healthy_regex", "won|active|discharged|completed|approved|paid")
    status_unhealthy = bus_term.get("status_unhealthy_regex", "lost|terminated|churned|inactive|overdue|failed")
    
    date_cols = sem_dict.get("date_columns", [])
    date_col = date_cols[0] if date_cols and date_cols[0] in df.columns else None
    
    def safe_divide(a, b):
        return a / b if b else 0.0

    def calc_trend(current, previous):
        if previous == 0 or pd.isna(previous):
            return 0.0
        # abs() on the baseline so a negative starting point (an overdrawn
        # balance, a loss) doesn't invert the sign of the reported change.
        return round(((current - previous) / abs(previous)) * 100, 1)
    
    if date_col:
        try:
            df[date_col] = to_datetime_safe(df[date_col])
            df = df.dropna(subset=[date_col])
            df = df.sort_values(by=date_col)
        except Exception:
            date_col = None

    recent_df = df
    prior_df = None
    
    if date_col:
        try:
            periods = df.groupby(df[date_col].dt.to_period('M'))
            if len(periods) >= 2:
                sorted_periods = sorted(periods.groups.keys())
                recent_df = periods.get_group(sorted_periods[-1])
                prior_df = periods.get_group(sorted_periods[-2])
        except Exception:
            pass

    # 1. Primary Metric KPI
    if primary_metric and primary_metric in original_df.columns:
        def agg_metric(subset_df):
            if subset_df.empty:
                return 0.0
            col_data = subset_df[primary_metric]
            if primary_op == "sum":
                return float(col_data.sum())
            elif primary_op == "mean":
                return float(col_data.mean())
            elif primary_op == "count":
                return float(col_data.count())
            elif primary_op == "nunique":
                return float(col_data.nunique())
            return float(col_data.sum())
            
        curr_val = agg_metric(original_df)
        
        # Calculate trend if date exists
        trend = 0.0
        prev_val = 0.0
        if prior_df is not None and not prior_df.empty:
            curr_period_val = agg_metric(recent_df)
            prior_period_val = agg_metric(prior_df)
            trend = calc_trend(curr_period_val, prior_period_val)
            prev_val = prior_period_val
            
        kpis.append({
            "id": "kpi_rev",
            "name": primary_label,
            "column": primary_metric,
            "value": round(curr_val, 2),
            "previous_value": round(prev_val, 2),
            "trend": trend,
            "type": primary_type,
            "history": []
        })

    # 2. Entity Count KPI
    if entity_col and entity_col in original_df.columns:
        # See compute_executive_kpis: a near-unique entity column is a per-row
        # reference, so the count is a count of rows. Counting distinct values
        # drops every row with a blank reference — the dashboard reported 1,372
        # transactions for a 1,411-row bank statement, and 39 of those rows have
        # no Ref No.
        try:
            entity_is_per_row = (
                original_df[entity_col].nunique(dropna=True) > len(original_df) * 0.9
            )
        except Exception:
            entity_is_per_row = False

        def agg_entity(subset_df):
            if subset_df.empty:
                return 0.0
            col_data = subset_df[entity_col]
            if pd.api.types.is_numeric_dtype(col_data) and not _ENTITY_ID_PATTERN.search(str(entity_col)):
                try:
                    return float(col_data.sum())
                except Exception:
                    return float(col_data.nunique())
            elif entity_is_per_row:
                return float(len(subset_df))
            else:
                return float(col_data.nunique())
                
        curr_val = agg_entity(original_df)
        
        trend = 0.0
        prev_val = 0.0
        if prior_df is not None and not prior_df.empty:
            curr_period_val = agg_entity(recent_df)
            prior_period_val = agg_entity(prior_df)
            trend = calc_trend(curr_period_val, prior_period_val)
            prev_val = prior_period_val
            
        kpis.append({
            "id": "kpi_users",
            "name": entity_label,
            "column": entity_col,
            "value": float(curr_val),
            "previous_value": float(prev_val),
            "trend": trend,
            "type": "count",
            "history": []
        })

    # 3. Secondary Metric KPI
    if secondary_metric and secondary_metric in original_df.columns:
        def agg_sec(subset_df):
            if subset_df.empty:
                return 0.0
            col_data = subset_df[secondary_metric]
            if secondary_op == "sum":
                return float(col_data.sum())
            elif secondary_op == "mean":
                return float(col_data.mean())
            elif secondary_op == "count":
                return float(col_data.count())
            elif secondary_op == "nunique":
                return float(col_data.nunique())
            return float(col_data.mean())
            
        curr_val = agg_sec(original_df)
        
        trend = 0.0
        prev_val = 0.0
        if prior_df is not None and not prior_df.empty:
            curr_period_val = agg_sec(recent_df)
            prior_period_val = agg_sec(prior_df)
            trend = calc_trend(curr_period_val, prior_period_val)
            prev_val = prior_period_val
            
        kpis.append({
            "id": "kpi_deal_size",
            "name": secondary_label,
            "column": secondary_metric,
            "value": round(curr_val, 2),
            "previous_value": round(prev_val, 2),
            "trend": trend,
            "type": secondary_type,
            "history": []
        })

    # 4. Status / Health KPI
    if status_col and status_col in original_df.columns:
        def calc_health(df_subset):
            if df_subset.empty:
                return 0.0
            s = df_subset[status_col].astype(str)
            healthy = s.str.contains(status_healthy, case=False, na=False)
            total = len(df_subset)
            if total > 0:
                return float(healthy.sum() / total * 100)
            return 0.0

            
        curr_health = calc_health(original_df)
        
        trend = 0.0
        prev_val = 0.0
        if prior_df is not None and not prior_df.empty:
            curr_period_val = calc_health(recent_df)
            prior_period_val = calc_health(prior_df)
            trend = calc_trend(curr_period_val, prior_period_val)
            prev_val = prior_period_val
            
        kpis.append({
            "id": "kpi_pipeline",
            "name": status_label,
            "column": status_col,
            "value": round(curr_health, 1),
            "previous_value": round(prev_val, 1),
            "trend": trend,
            "type": "percent",
            "history": []
        })

    # 5. Additional numeric-column KPIs — the 4 above are auto-detected from
    # semantic classification, but the dashboard-customization feature needs
    # a real pool of candidates for users to choose/pin beyond those 4.
    used_cols = {c for c in (primary_metric, entity_col, secondary_metric, status_col) if c}
    extra_numeric_cols = [
        c for c in original_df.select_dtypes(include="number").columns
        if c not in used_cols
    ]
    MAX_EXTRA_KPIS = 12
    for col in extra_numeric_cols[:MAX_EXTRA_KPIS]:
        col_op = "mean" if is_non_additive(col) else "sum"

        def agg_extra(subset_df, _col=col, _op=col_op):
            if subset_df.empty:
                return 0.0
            data = subset_df[_col]
            return float(data.mean()) if _op == "mean" else float(data.sum())

        curr_val = agg_extra(original_df)

        trend = 0.0
        prev_val = 0.0
        if prior_df is not None and not prior_df.empty:
            trend = calc_trend(agg_extra(recent_df), agg_extra(prior_df))
            prev_val = agg_extra(prior_df)

        kpis.append({
            "id": f"col_{col}",
            "name": col.replace("_", " ").replace("-", " ").title(),
            "column": col,
            "agg": col_op,
            "value": round(curr_val, 2),
            "previous_value": round(prev_val, 2),
            "trend": trend,
            # Typing every extra column "generic" strips the currency symbol
            # from columns that plainly hold money (Debit, bill_amount,
            # salary), so a bank dashboard shows "₹58.82L" for one rupee
            # column next to a bare number for another. Infer money from the
            # column name so the unit shown matches what the figure is.
            "type": "currency" if is_money_like(col) else "generic",
            "history": []
        })

    chart_data = []
    if date_col and primary_metric and primary_metric in df.columns:
        try:
            if primary_op == "mean":
                grouped_res = df.groupby(df[date_col].dt.strftime('%b %Y'))[primary_metric].mean().reset_index()
            else:
                grouped_res = df.groupby(df[date_col].dt.strftime('%b %Y'))[primary_metric].sum().reset_index()
                
            grouped_res['temp_date'] = pd.to_datetime(grouped_res[date_col], format='%b %Y')
            grouped_res = grouped_res.sort_values(by='temp_date')
            for _, row in grouped_res.iterrows():
                chart_data.append({
                    "name": row[date_col],
                    "value": round(float(row[primary_metric]), 2)
                })
                
            fc = forecast_series(df, primary_metric, periods=2)
            if fc.get("available"):
                if chart_data:
                    chart_data[-1]["forecast"] = chart_data[-1]["value"]
                existing_labels = {c["name"] for c in chart_data}
                for f_point in fc.get("forecast", []):
                    label = f_point["date"]
                    # forecast_series() drops a trailing part-month from its
                    # training data and re-estimates it as the first forecast
                    # point, so that point can carry the same label as the last
                    # actual month. Left alone the chart plots two different
                    # values under one x-axis label; tag it as the revised
                    # estimate it actually is.
                    if label in existing_labels:
                        label = f"{label} (Revised Est.)"
                    existing_labels.add(label)
                    chart_data.append({
                        "name": label,
                        "value": None,
                        "forecast": round(f_point["forecast"], 2)
                    })
        except Exception:
            pass
            
    # Populate history for KPIs based on date_col grouping if possible
    if date_col:
        try:
            df_temp = df.dropna(subset=[date_col]).copy()
            periods_list = df_temp.groupby(df_temp[date_col].dt.to_period('M'))
            
            for k in kpis:
                hist = []
                sorted_p = sorted(periods_list.groups.keys())
                for p in sorted_p:
                    group_df = periods_list.get_group(p)
                    val = 0.0
                    
                    if k["id"] == "kpi_rev" and primary_metric and primary_metric in group_df.columns:
                        if primary_op == "mean":
                            val = group_df[primary_metric].mean()
                        else:
                            val = group_df[primary_metric].sum()
                            
                    elif k["id"] == "kpi_users" and entity_col and entity_col in group_df.columns:
                        val = agg_entity(group_df)
                            
                    elif k["id"] == "kpi_deal_size" and secondary_metric and secondary_metric in group_df.columns:
                        val = agg_sec(group_df)
                        
                    elif k["id"] == "kpi_pipeline" and status_col and status_col in group_df.columns:
                        val = calc_health(group_df)

                    elif k["id"].startswith("col_") and k.get("column") in group_df.columns:
                        col_data = group_df[k["column"]]
                        val = col_data.mean() if k.get("agg") == "mean" else col_data.sum()

                    hist.append({"date": p.strftime('%b %Y'), "value": round(float(val), 2)})
                
                k["history"] = hist
        except Exception:
            pass

    return {"kpis": kpis, "chart_data": chart_data}


def compute_executive_kpis(df: pd.DataFrame, semantic_dict: dict = None) -> dict:
    if df is None:
        return {"kpis": [], "chart_data": []}
        
    if not semantic_dict:
        from app.services.semantic_classification import fallback_classify
        _, semantic_dict = fallback_classify(df, "Active Dataset")
    else:
        from app.services.semantic_classification import validate_and_sanitize_business_terminology
        domain = semantic_dict.get("domain", "generic")
        bus_term = semantic_dict.get("business_terminology", {})
        validate_and_sanitize_business_terminology(df, domain, bus_term)
        
    # get_dataframe() hands back the shared cached frame, so writing the parsed
    # date column straight onto `df` (below) would mutate that cache in place —
    # every later request, for every other endpoint, would then read a frame
    # whose date column had already been converted. Work on our own copy.
    df = df.copy()
    original_df = df.copy()
    kpis = []
    
    bus_term = semantic_dict.get("business_terminology", {})
    sem_dict = semantic_dict.get("semantic_dictionary", {})
    
    primary_metric = bus_term.get("primary_metric")
    primary_label = bus_term.get("primary_metric_label", "Primary Metric")
    primary_op = bus_term.get("primary_metric_op", "sum")
    primary_type = bus_term.get("primary_metric_type", "generic")
    
    entity_col = bus_term.get("entity_col")
    entity_label = bus_term.get("entity_count_label", "Volume Metric")
    
    secondary_metric = bus_term.get("secondary_metric")
    secondary_label = bus_term.get("secondary_metric_label", "Efficiency Metric")
    secondary_op = bus_term.get("secondary_metric_op", "mean")
    secondary_type = bus_term.get("secondary_metric_type", "generic")
    
    status_col = bus_term.get("status_col")
    status_label = bus_term.get("status_metric_label", "Health Metric")
    status_healthy = bus_term.get("status_healthy_regex", "won|active|discharged|completed|approved|paid")
    
    date_cols = sem_dict.get("date_columns", [])
    date_col = date_cols[0] if date_cols and date_cols[0] in df.columns else None
    
    if date_col:
        try:
            df[date_col] = to_datetime_safe(df[date_col])
            df = df.dropna(subset=[date_col])
            df = df.sort_values(by=date_col)
        except Exception:
            date_col = None

    recent_df = df
    prior_df = None
    comparison_period = "Dataset Average"
    reporting_period = "All Time"
    
    if date_col:
        try:
            periods = df.groupby(df[date_col].dt.to_period('M'))
            if len(periods) >= 2:
                sorted_periods = sorted(periods.groups.keys())
                recent_df = periods.get_group(sorted_periods[-1])
                prior_df = periods.get_group(sorted_periods[-2])
                reporting_period = sorted_periods[-1].strftime('%B %Y')
                comparison_period = sorted_periods[-2].strftime('%B %Y')
            elif len(periods) == 1:
                reporting_period = list(periods.groups.keys())[0].strftime('%B %Y')
                comparison_period = "No prior history"
        except Exception:
            pass

    def build_kpi(category, name, col, op, val_type, calc_fn):
        if not col or col not in original_df.columns:
            return None
            
        curr_val = calc_fn(original_df) if not date_col else calc_fn(recent_df)
        prev_val = calc_fn(original_df) if not date_col else (calc_fn(prior_df) if prior_df is not None else curr_val)
        
        diff = None
        perc = None
        trend_dir = "flat"
        
        if date_col and prior_df is not None:
            diff = curr_val - prev_val
            if prev_val != 0 and not pd.isna(prev_val):
                # Divide by the magnitude of the baseline, not its signed value.
                # On an overdrawn account a balance moving from -1.05Cr to
                # -1.08Cr gave (-3.73L / -1.05Cr) = +3.6%, so the card showed a
                # green "+3.6%" and an upward arrow next to a delta of -3.73L
                # for a position that had got worse.
                perc = (diff / abs(prev_val)) * 100
            else:
                perc = 0.0
            # Direction follows the actual movement, which stays correct
            # whatever the sign of the baseline.
            if diff > 0: trend_dir = "up"
            elif diff < 0: trend_dir = "down"
        
        history = {
            "monthly": [],
            "quarterly": [],
            "yearly": []
        }
        if date_col:
            import math
            def safe_val(grp):
                try:
                    v = float(calc_fn(grp))
                    return 0.0 if math.isnan(v) or math.isinf(v) else round(v, 2)
                except:
                    return 0.0

            try:
                for p, grp in df.groupby(df[date_col].dt.to_period('M')):
                    history["monthly"].append({"name": p.strftime('%b %Y'), "value": safe_val(grp)})
                for p, grp in df.groupby(df[date_col].dt.to_period('Q')):
                    history["quarterly"].append({"name": f"Q{p.quarter} {p.year}", "value": safe_val(grp)})
                for p, grp in df.groupby(df[date_col].dt.to_period('Y')):
                    history["yearly"].append({"name": str(p.year), "value": safe_val(grp)})
            except Exception as e:
                print("Error generating history:", e)
            
        return {
            "category": category,
            "name": name,
            "current": round(float(curr_val), 2),
            "previous": round(float(prev_val), 2) if date_col and prior_df is not None else None,
            "difference": round(float(diff), 2) if diff is not None else None,
            "percentage": round(float(perc), 1) if perc is not None else None,
            "trend": trend_dir if diff is not None else None,
            "history": history,
            "coverage": round((1 - original_df[col].isna().mean()) * 100, 1),
            "rows_used": int(len(original_df) if not date_col else len(recent_df)),
            "aggregation": op,
            "query_id": f"q_{category.lower()}_{np.random.randint(1000, 9999)}",
            # Scales continuously with actual completeness instead of a binary
            # "any missing at all" cliff (100% coverage -> 95, same anchor as
            # before; a column that's 1% missing no longer scores identically
            # to one that's 60% missing).
            "confidence": round(50 + 0.45 * ((1 - original_df[col].isna().mean()) * 100), 1),
            "last_refresh": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "source_column": col,
            "formula": f"{op.upper()}({col})",
            "type": val_type,
            "rationale": f"Automatically identified as the optimal {category} metric with high semantic confidence.",
            "insight": f"{name} showed a {trend_dir} trend compared to previous reporting period." if diff is not None else "Consistent metric over time.",
            "reporting_period": reporting_period,
            "comparison_period": comparison_period,
            "drilldown_metadata": {"col": col, "op": op}
        }

    if primary_metric:
        def calc_prim(d):
            if d.empty: return 0.0
            if primary_op == "sum": return float(d[primary_metric].sum())
            if primary_op == "mean": return float(d[primary_metric].mean())
            return float(d[primary_metric].count())
        k = build_kpi("Primary", primary_label, primary_metric, primary_op, primary_type, calc_prim)
        if k: kpis.append(k)

    if entity_col:
        # Decide once, over the whole dataset, whether the entity column is a
        # per-row reference or a repeating dimension. A reference number is
        # near-unique, so the thing being counted is rows: counting distinct
        # values instead silently drops any row whose reference is blank — one
        # missing "Ref No" turned 47 June transactions into "46". A repeating
        # dimension like customer_id genuinely wants distinct values, or an
        # orders table would report "Total Customers" as its order count.
        try:
            entity_is_per_row = (
                original_df[entity_col].nunique(dropna=True) > len(original_df) * 0.9
            )
        except Exception:
            entity_is_per_row = False

        def calc_vol(d):
            if d.empty: return 0.0
            col_data = d[entity_col]
            if pd.api.types.is_numeric_dtype(col_data) and not _ENTITY_ID_PATTERN.search(str(entity_col)):
                try: return float(col_data.sum())
                except: return float(col_data.nunique())
            if entity_is_per_row:
                return float(len(d))
            return float(col_data.nunique())
        k = build_kpi("Volume", entity_label, entity_col, "count", "count", calc_vol)
        if k: kpis.append(k)

    if secondary_metric:
        def calc_sec(d):
            if d.empty: return 0.0
            if secondary_op == "sum": return float(d[secondary_metric].sum())
            if secondary_op == "mean": return float(d[secondary_metric].mean())
            return float(d[secondary_metric].count())
        k = build_kpi("Efficiency", secondary_label, secondary_metric, secondary_op, secondary_type, calc_sec)
        if k: kpis.append(k)

    if status_col:
        def calc_health(d):
            if d.empty: return 0.0
            s = d[status_col].astype(str)
            healthy = s.str.contains(status_healthy, case=False, na=False)
            total = len(d)
            if total > 0: return float(healthy.sum() / total * 100)
            return 0.0
        k = build_kpi("Health", status_label, status_col, "ratio", "percent", calc_health)
        if k: kpis.append(k)

    chart_data = []
    if date_col and primary_metric and primary_metric in df.columns:
        try:
            if primary_op == "mean":
                grouped_res = df.groupby(df[date_col].dt.strftime('%b %Y'))[primary_metric].mean().reset_index()
            else:
                grouped_res = df.groupby(df[date_col].dt.strftime('%b %Y'))[primary_metric].sum().reset_index()
                
            grouped_res['temp_date'] = pd.to_datetime(grouped_res[date_col], format='%b %Y')
            grouped_res = grouped_res.sort_values(by='temp_date')
            for _, row in grouped_res.iterrows():
                chart_data.append({
                    "name": row[date_col],
                    "value": round(float(row[primary_metric]), 2)
                })
                
            fc = forecast_series(df, primary_metric, periods=2)
            if fc.get("available"):
                if chart_data:
                    chart_data[-1]["forecast"] = chart_data[-1]["value"]
                existing_labels = {c["name"] for c in chart_data}
                for f_point in fc.get("forecast", []):
                    label = f_point["date"]
                    # forecast_series() drops a trailing part-month from its
                    # training data and re-estimates it as the first forecast
                    # point, so that point can carry the same label as the last
                    # actual month. Left alone the chart plots two different
                    # values under one x-axis label; tag it as the revised
                    # estimate it actually is.
                    if label in existing_labels:
                        label = f"{label} (Revised Est.)"
                    existing_labels.add(label)
                    chart_data.append({
                        "name": label,
                        "value": None,
                        "forecast": round(f_point["forecast"], 2)
                    })
        except Exception:
            pass

    return {"kpis": kpis, "chart_data": chart_data}


def quality_report(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {"quality_score": 0, "breakdown": {"completeness": 0, "uniqueness": 0, "type_consistency": 0, "validity": 0}}
        
    completeness = (1 - df.isna().mean().mean()) * 100
    
    # Uniqueness (simplified to row duplication ratio)
    dup_ratio = df.duplicated().mean()
    uniqueness = (1 - dup_ratio) * 100
    
    # Type consistency (percent of columns with single inferred type)
    # For a simple mock, we'll give 100% minus 5% for each object column that has mixed types.
    type_consistency = 100.0
    for col in df.columns:
        if df[col].dtype == 'object':
            types = df[col].dropna().map(type).nunique()
            if types > 1:
                type_consistency -= 5.0
    type_consistency = max(0.0, type_consistency)
    
    # Validity (are numeric values within expected ranges? - mock)
    validity = 100.0
    
    score = (completeness + uniqueness + type_consistency + validity) / 4
    
    return {
        "quality_score": float(score),
        "breakdown": {
            "completeness": float(completeness),
            "uniqueness": float(uniqueness),
            "type_consistency": float(type_consistency),
            "validity": float(validity)
        }
    }


# ─── Metric importance/confidence scoring ──────────────────────────────────
# These factor weights (e.g. sample size worth up to 30pts, distribution
# stability up to 25pts) are a design choice, not something derivable from
# data - there's no labeled ground truth for "how important is this metric"
# to calibrate against, so the weights themselves are left as-is rather than
# swapping one arbitrary allocation for another. What WAS a real bug: each
# factor was scored with hardcoded step-function thresholds (e.g. n>=100 vs
# n=99 scoring very differently despite being practically identical). The
# functions below replace those cliffs with continuous interpolation between
# the same anchor points, so near-identical inputs get near-identical scores.

def _smooth_score(x: float, anchors_x: list, anchors_y: list, log_scale: bool = False) -> float:
    """Piecewise-linear interpolation between (x, y) anchor points, clamped
    to the first/last y value outside the anchor range."""
    if x <= anchors_x[0]:
        return anchors_y[0]
    if x >= anchors_x[-1]:
        return anchors_y[-1]
    xs = [np.log(v) for v in anchors_x] if log_scale else anchors_x
    xv = np.log(x) if log_scale else x
    return float(np.interp(xv, xs, anchors_y))


def sample_adequacy_score(n: int) -> float:
    """0-30 pts, continuous in log(n). Anchored at the same reference points
    a fixed n>=X bucket table used to use (n=1000->30 ... n<10->~1)."""
    if n <= 0:
        return 0.0
    return _smooth_score(n, [1, 10, 30, 100, 500, 1000], [1, 8, 15, 20, 25, 30], log_scale=True)


def distribution_stability_score(ks_p: float) -> float:
    """0-25 pts, continuous in the KS-test p-value (higher p = more stable/
    similar first-half-vs-second-half distribution = higher confidence)."""
    return _smooth_score(ks_p, [0.0, 0.01, 0.05, 0.1], [5, 12, 20, 25])


def outlier_ratio_score(outlier_ratio: float) -> float:
    """0-20 pts, continuous in the fraction of rows flagged as outliers."""
    return _smooth_score(outlier_ratio, [0.0, 0.01, 0.05, 0.2], [20, 16, 10, 3])


def cv_stability_score(cv: float) -> float:
    """0-10 pts, continuous in the coefficient of variation (std/mean)."""
    return _smooth_score(cv, [0.0, 0.5, 1.0, 2.0], [10, 7, 4, 1])


def compute_metric_confidence(n: int, coverage_pct: float, ks_p: float = None,
                               outlier_ratio: float = None, cv: float = None) -> int:
    """
    Combines the four factors above into the same 0-100 confidence score
    used by /analytics/metrics and /analytics/metrics/{metric}/intelligence
    (previously duplicated inline in both, with hardcoded step-function
    thresholds in each copy).
    """
    score = sample_adequacy_score(n)
    score += distribution_stability_score(ks_p) if ks_p is not None else 12.0
    score += outlier_ratio_score(outlier_ratio) if outlier_ratio is not None else 10.0
    score += (coverage_pct / 100) * 15
    if cv is not None:
        score += cv_stability_score(cv)
    return int(min(100, max(5, round(score))))


def compute_metric_importance(variance_share: float = None, avg_corr: float = None,
                               max_corr: float = None, norm_entropy: float = None,
                               temporal_r2: float = None, temporal_significant: bool = False) -> int:
    """
    Combines variance contribution / cross-correlation / entropy / temporal
    signal into the same 0-100 importance score used by both /analytics
    endpoints above (previously duplicated inline in each).
    """
    score = 0.0
    if variance_share is not None:
        score += min(25, variance_share * 100)
    if avg_corr is not None:
        score += avg_corr * 15 + (10 if (max_corr or 0) > 0.5 else 0)
    if norm_entropy is not None:
        score += norm_entropy * 25
    else:
        score += 12
    if temporal_r2 is not None:
        score += temporal_r2 * 20
        if temporal_significant:
            score += 5
    return int(min(100, max(10, round(score))))


# One full seasonal cycle per resampling frequency: a week of days, a year
# of weeks/months/quarters. Holt-Winters needs two of these to fit at all.
_SEASONAL_PERIODS = {"D": 7, "W": 52, "M": 12, "Q": 4}

_SEASON_LABEL = {
    "D": "weekly seasonality",
    "W": "yearly seasonality",
    "M": "yearly seasonality",
    "Q": "yearly seasonality",
}


def _fit_forecast_model(y: np.ndarray, periods: int, freq: str = "M"):
    """
    Fits the best model the series' length supports and returns
    (forecast_array, in_sample_residuals, method_label, k_params).

    Tries progressively simpler models and NEVER raises: seasonal
    Holt-Winters needs 2 full cycles at the series' own frequency, plain
    Holt trend needs a handful of points, and a short series falls back to
    OLS linear trend (the only method the original implementation had).
    """
    n = len(y)
    seasonal_periods = _SEASONAL_PERIODS.get(freq, 12)

    if n >= 2 * seasonal_periods:
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            fit = ExponentialSmoothing(
                y, trend='add', seasonal='add', seasonal_periods=seasonal_periods,
                initialization_method='estimated'
            ).fit()
            fc = np.asarray(fit.forecast(periods), dtype=float)
            resid = np.asarray(fit.resid, dtype=float)
            if np.all(np.isfinite(fc)) and np.all(np.isfinite(resid)) and len(resid) > 0:
                label = "Holt-Winters (trend + %s)" % _SEASON_LABEL.get(freq, "seasonality")
                return fc, resid, label, seasonal_periods + 2
        except Exception:
            pass

    if n >= 8:
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            fit = ExponentialSmoothing(
                y, trend='add', seasonal=None,
                initialization_method='estimated'
            ).fit()
            fc = np.asarray(fit.forecast(periods), dtype=float)
            resid = np.asarray(fit.resid, dtype=float)
            if np.all(np.isfinite(fc)) and np.all(np.isfinite(resid)) and len(resid) > 0:
                return fc, resid, "Holt linear trend (double exponential smoothing)", 2
        except Exception:
            pass

    # Fallback for short series (4-7 points) or if the fancier fits above failed
    x = np.arange(n)
    p = np.polyfit(x, y, 1)
    m, b = float(p[0]), float(p[1])
    resid = y - (m * x + b)
    fc = np.array([m * (n - 1 + i) + b for i in range(1, periods + 1)])
    return fc, resid, "Linear trend projection (OLS)", 2


def _backtest_forecast_accuracy(y: np.ndarray, freq: str = "M") -> Optional[dict]:
    """
    Holds out the last few points, refits on the rest, and scores the
    holdout predictions with MAPE/RMSE. Returns None when there isn't
    enough history left after the split for the comparison to mean anything.
    """
    n = len(y)
    holdout = min(3, max(1, n // 5))
    if n - holdout < 4:
        return None

    train, test = y[:-holdout], y[-holdout:]
    try:
        fc, _, method_label, _ = _fit_forecast_model(train, holdout, freq)
    except Exception:
        return None

    if not np.all(np.isfinite(fc)):
        return None

    abs_err = np.abs(test - fc)
    rmse = float(np.sqrt(np.mean(abs_err ** 2)))

    nonzero = test != 0
    mape = float(np.mean(abs_err[nonzero] / np.abs(test[nonzero])) * 100) if nonzero.any() else None

    return {
        "mape": round(mape, 2) if mape is not None else None,
        "rmse": round(rmse, 2),
        "holdout_periods": int(holdout),
        "method": method_label
    }


_FREQ_LABEL = {"D": "day", "W": "week", "M": "month", "Q": "quarter"}


def _format_period(period, freq: str) -> str:
    """Human label for a pandas Period at the given resampling frequency."""
    if freq == "Q":
        return "Q%d %d" % (period.quarter, period.year)
    if freq == "D":
        return period.strftime('%d %b %Y')
    if freq == "W":
        return "w/c %s" % period.start_time.strftime('%d %b %Y')
    return period.strftime('%b %Y')


def _auto_freq(dates: pd.Series) -> str:
    """Pick the finest frequency the history can actually support.

    Forecasting needs at least a handful of populated buckets, so step down
    from daily only when the span is too short to give monthly enough of them.
    """
    span_days = (dates.max() - dates.min()).days
    if span_days <= 0:
        return "M"
    if span_days < 60:
        return "D"
    if span_days < 180:
        return "W"
    if span_days < 730:
        return "M"
    return "Q"


def forecast_series(
    df: pd.DataFrame,
    metric_col: str,
    periods: int = 3,
    agg: str = "sum",
    freq: str = "M",
) -> dict:
    if df.empty:
        return {"available": False, "reason": "Empty dataset"}

    actual_col = next((c for c in df.columns if c.lower() == metric_col.lower()), None)
    if not actual_col or not pd.api.types.is_numeric_dtype(df[actual_col]):
        return {"available": False, "reason": "Invalid metric column"}

    metric_col = actual_col

    date_col = find_column(df, r'date|month|year|time')
    if not date_col:
         return {"available": False, "reason": "No date column found"}

    df_temp = df.copy()
    df_temp[date_col] = to_datetime_safe(df_temp[date_col])
    df_temp = df_temp.dropna(subset=[date_col])

    if df_temp.empty:
        return {"available": False, "reason": "No parseable dates in the date column"}

    freq = str(freq).upper()
    if freq == "AUTO":
        freq = _auto_freq(df_temp[date_col])
    if freq not in _SEASONAL_PERIODS:
        freq = "M"

    agg_fn = "mean" if str(agg).lower() == "mean" else "sum"
    grouped = df_temp.groupby(df_temp[date_col].dt.to_period(freq))[metric_col].agg(agg_fn).reset_index()
    grouped = grouped.sort_values(date_col)

    # A dataset that ends mid-period leaves a final bucket holding only part of
    # its days. Summed, that reads as a collapse in the metric — it drags the
    # trend fit down, poisons the backtest, and makes the headline change wildly
    # wrong. Averages stay valid over a short bucket, so only sums are trimmed.
    partial_period_dropped = None
    if agg_fn == "sum" and len(grouped) > 4:
        last_period = grouped[date_col].iloc[-1]
        if last_period.end_time.normalize() > df_temp[date_col].max().normalize():
            partial_period_dropped = _format_period(last_period, freq)
            grouped = grouped.iloc[:-1]

    if len(grouped) < 4:
        return {
            "available": False,
            "reason": "Not enough history at %sly granularity (%d period%s, need at least 4)"
                      % (_FREQ_LABEL[freq], len(grouped), "" if len(grouped) == 1 else "s"),
        }

    y = grouped[metric_col].values.astype(float)
    n = len(y)
    last_date = grouped[date_col].iloc[-1]

    accuracy = _backtest_forecast_accuracy(y, freq)
    fc_values, resid, method_label, k_params = _fit_forecast_model(y, periods, freq)

    sse = float(np.sum(resid ** 2))
    df_err = max(1, n - k_params)
    std_err = np.sqrt(sse / df_err) if sse > 0 else 0.0
    t_val = float(scipy_stats.t.ppf(0.975, df_err))

    forecast_values = []
    for i in range(1, periods + 1):
        fy = float(fc_values[i - 1])
        # Widen the interval the further out the forecast reaches
        moe = t_val * std_err * np.sqrt(1 + i / n) if std_err > 0 else 0.0
        next_period = last_date + i

        forecast_values.append({
            "date": _format_period(next_period, freq),
            "forecast": fy,
            "lower": float(max(0, fy - moe)) if fy >= 0 else float(fy - moe),
            "upper": float(fy + moe)
        })

    historical_values = []
    for _, row in grouped.iterrows():
        historical_values.append({
            "date": _format_period(row[date_col], freq),
            "value": float(row[metric_col])
        })

    # Headline numbers the UI would otherwise have to re-derive from the series.
    last_actual = float(y[-1])
    next_value = float(fc_values[0])
    # Trimming a part-period above means the first projected period is that same
    # still-running one, so it is a completion of the current period rather than
    # a step into the next. The UI labels the two cases differently.
    next_is_in_progress = (
        partial_period_dropped is not None
        and forecast_values[0]["date"] == partial_period_dropped
    )
    summary = {
        "last_actual": last_actual,
        "next_value": next_value,
        "next_label": forecast_values[0]["date"],
        "next_is_in_progress": next_is_in_progress,
        "change_pct": round(((next_value - last_actual) / abs(last_actual)) * 100, 2) if last_actual else None,
        "horizon_total": float(np.sum(fc_values)),
        "history_periods": n,
    }

    return {
        "available": True,
        "method": method_label,
        "freq": freq,
        "freq_label": _FREQ_LABEL[freq],
        "periods": periods,
        "historical": historical_values,
        "forecast": forecast_values,
        "accuracy": accuracy,
        "summary": summary,
        "partial_period_dropped": partial_period_dropped,
    }
