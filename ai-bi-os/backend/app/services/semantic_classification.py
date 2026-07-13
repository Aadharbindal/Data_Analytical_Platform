import os
import re
import json
import logging
import pandas as pd
import numpy as np
from litellm import completion
from app.core.config import LLM_MODEL

def validate_and_sanitize_business_terminology(df: pd.DataFrame, domain: str, bus_term: dict):
    entity_col = bus_term.get("entity_col")
    entity_label = bus_term.get("entity_count_label", "Total Items")
    
    if entity_col and entity_col not in df.columns:
        entity_col = None
        
    if not entity_col:
        id_cols = [c for c in df.columns if re.search(r'\b(id|key|code|uuid|number|num)\b|_id$', str(c).lower())]
        if id_cols:
            entity_col = id_cols[0]
        else:
            entity_col = df.columns[0]
            
    bus_term["entity_col"] = entity_col
    
    if entity_col:
        ent_lower = str(entity_col).lower()
        if "transaction" in entity_label.lower() or "order" in entity_label.lower() or "deal" in entity_label.lower() or "txn" in entity_label.lower():
            # If counting unique of user-specific ID but calling it transactions/orders/deals, switch to actual transaction reference ID
            txn_id_col = next((c for c in df.columns if re.search(r'\b(utr|ref|reference|txn_id|txnid|order_id|invoice_id|trans_id)\b', str(c).lower())), None)
            if txn_id_col and txn_id_col != entity_col:
                entity_col = txn_id_col
                bus_term["entity_col"] = entity_col
                ent_lower = str(entity_col).lower()
                
        if any(x in ent_lower for x in ["transaction", "txn", "utr", "ref"]):
            bus_term["entity_count_label"] = "Total Transactions"
        elif "order" in ent_lower or "invoice" in ent_lower:
            bus_term["entity_count_label"] = "Total Orders"
        elif "upi" in ent_lower:
            bus_term["entity_count_label"] = "Total UPI Users"
        elif "account" in ent_lower:
            bus_term["entity_count_label"] = "Total Accounts"
        elif "customer" in ent_lower or "client" in ent_lower:
            bus_term["entity_count_label"] = "Total Customers"
        elif "employee" in ent_lower or "staff" in ent_lower:
            bus_term["entity_count_label"] = "Total Employees"
        elif "patient" in ent_lower:
            bus_term["entity_count_label"] = "Total Patients"
        elif "lead" in ent_lower or "opportunity" in ent_lower:
            bus_term["entity_count_label"] = "Total Leads"
        elif "campaign" in ent_lower:
            bus_term["entity_count_label"] = "Total Campaigns"
        elif "product" in ent_lower or "sku" in ent_lower or "item" in ent_lower:
            bus_term["entity_count_label"] = "Total Products"
        else:
            is_user_col = any(x in ent_lower for x in ["user", "customer", "client", "member", "employee", "staff", "account", "upi", "card", "email", "phone"])
            if is_user_col and ("transaction" in entity_label.lower() or "order" in entity_label.lower()):
                bus_term["entity_count_label"] = "Total Unique Users"
            else:
                bus_term["entity_count_label"] = entity_label
    else:
        bus_term["entity_count_label"] = "Total Records"

def fallback_classify(df: pd.DataFrame, filename: str) -> tuple[str, dict]:
    """
    Rule-based fallback classifier in case the LLM is unavailable or fails.
    """
    cols = [str(c) for c in df.columns]
    cols_lower = [c.lower() for c in cols]
    filename_lower = filename.lower()
    
    # 1. Detect Domain
    domain = "generic"
    
    if any(re.search(r'employee|salary|headcount|hired|termination|hr\b|staff|job_title|department|workforce|attrition', c) for c in cols_lower) or "hr" in filename_lower or "employee" in filename_lower or "staff" in filename_lower:
        domain = "HR"
    elif any(re.search(r'patient|admission|diagnosis|doctor|hospital|clinic|treatment|physician|readmission|medical', c) for c in cols_lower) or "health" in filename_lower or "patient" in filename_lower or "clinical" in filename_lower:
        domain = "healthcare"
    elif any(re.search(r'stock|warehouse|sku\b|inventory|reorder|supplier|product_count|quantity_on_hand|replenish', c) for c in cols_lower) or "inventory" in filename_lower or "stock" in filename_lower or "warehouse" in filename_lower:
        domain = "inventory"
    elif any(re.search(r'campaign|click|impression|ctr\b|spend|ad_|cpc\b|cpa\b|conversion|marketing|roas', c) for c in cols_lower) or "marketing" in filename_lower or "ad_" in filename_lower or "campaign" in filename_lower:
        domain = "marketing"
    elif any(re.search(r'lead|opportunity|funnel|contact|pipeline|deal_stage|stage', c) for c in cols_lower) or "crm" in filename_lower or "lead" in filename_lower or "deal" in filename_lower:
        domain = "CRM"
    elif any(re.search(r'balance|deposit|loan|interest|account_type|checking|saving|withdrawal|transaction_type', c) for c in cols_lower) or "bank" in filename_lower or "account" in filename_lower or "transaction" in filename_lower:
        domain = "banking"
    elif any(re.search(r'expense|assets|liabilities|equity|invoice|tax|budget|cash_flow|profit_loss|capital', c) for c in cols_lower) or "finance" in filename_lower or "financial" in filename_lower or "budget" in filename_lower:
        domain = "finance"
    elif any(re.search(r'sales|revenue|amount|price|order|customer|quantity|profit|deal_size|discount', c) for c in cols_lower) or "sales" in filename_lower or "revenue" in filename_lower or "order" in filename_lower:
        domain = "sales"
        
    # 2. Build semantic dictionary categories
    date_cols = []
    num_metrics = []
    cat_fields = []
    entity_ids = []
    status_fields = []
    geo_fields = []
    
    for col in cols:
        col_lower = col.lower()
        
        # Check datetime types
        is_dt = False
        try:
            if pd.api.types.is_datetime64_any_dtype(df[col]) or pd.api.types.is_datetime64tz_dtype(df[col]):
                is_dt = True
        except:
            pass
            
        if is_dt or re.search(r'\b(date|month|year|time|timestamp|day|hour|created_at|updated_at)\b', col_lower):
            date_cols.append(col)
        elif re.search(r'\b(id|key|code|uuid|number|num|phone|zip|postal|ref|reference|utr)\b|_id$|id$|^id', col_lower):
            entity_ids.append(col)
        elif re.search(r'\b(status|stage|state|phase|step|outcome)\b', col_lower):
            status_fields.append(col)
        elif re.search(r'\b(country|city|state|region|location|address|zip|postal|lat|long|latitude|longitude)\b', col_lower):
            geo_fields.append(col)
        else:
            is_numeric = False
            try:
                is_numeric = pd.api.types.is_numeric_dtype(df[col])
            except:
                pass
            if is_numeric:
                num_metrics.append(col)
            else:
                cat_fields.append(col)
                
    # 3. Formulate Domain-specific Terminology
    bus_term = {}
    if domain == "HR":
        primary = next((m for m in num_metrics if "salary" in m.lower() or "compensation" in m.lower()), None)
        bus_term = {
            "dashboard_title": "Workforce & HR Operations Hub",
            "primary_metric": primary if primary else "headcount",
            "primary_metric_label": f"Total {primary}" if primary else "Total Headcount",
            "primary_metric_op": "sum" if primary else "count",
            "primary_metric_type": "currency" if primary else "count",
            "entity_col": entity_ids[0] if entity_ids else (cat_fields[0] if cat_fields else "employee"),
            "entity_count_label": "Total Employees",
            "secondary_metric": primary if primary else None,
            "secondary_metric_label": f"Average {primary}" if primary else None,
            "secondary_metric_op": "mean" if primary else None,
            "secondary_metric_type": "currency" if primary else None,
            "status_col": status_fields[0] if status_fields else None,
            "status_metric_label": "Employee Active Rate" if status_fields else None,
            "status_healthy_regex": "Active|Hired|Full",
            "status_unhealthy_regex": "Terminated|Resigned|Inactive",
            "chart_title": "Headcount Trend"
        }
    elif domain == "healthcare":
        primary = next((m for m in num_metrics if "cost" in m.lower() or "charge" in m.lower() or "stay" in m.lower()), None)
        bus_term = {
            "dashboard_title": "Patient Care & Clinical Analytics Portal",
            "primary_metric": primary if primary else "patients",
            "primary_metric_label": f"Total {primary}" if primary else "Patient Visits",
            "primary_metric_op": "sum" if primary else "count",
            "primary_metric_type": "currency" if primary and ("cost" in primary.lower() or "charge" in primary.lower()) else "count",
            "entity_col": entity_ids[0] if entity_ids else (cat_fields[0] if cat_fields else "patient"),
            "entity_count_label": "Total Patients",
            "secondary_metric": primary if primary else None,
            "secondary_metric_label": f"Average {primary}" if primary else None,
            "secondary_metric_op": "mean" if primary else None,
            "secondary_metric_type": "generic" if primary else None,
            "status_col": status_fields[0] if status_fields else None,
            "status_metric_label": "Discharged Patient Ratio" if status_fields else None,
            "status_healthy_regex": "Discharged|Completed|Recovered|Active",
            "status_unhealthy_regex": "Failed|Cancelled|Critical",
            "chart_title": "Patient Visit Progression"
        }
    elif domain == "inventory":
        primary = next((m for m in num_metrics if "quantity" in m.lower() or "stock" in m.lower() or "value" in m.lower() or "cost" in m.lower()), (num_metrics[0] if num_metrics else None))
        bus_term = {
            "dashboard_title": "Inventory Control & Logistics Hub",
            "primary_metric": primary if primary else "stock_level",
            "primary_metric_label": f"Stock {primary}" if primary else "Total Items",
            "primary_metric_op": "sum",
            "primary_metric_type": "currency" if primary and ("cost" in primary.lower() or "price" in primary.lower() or "value" in primary.lower()) else "count",
            "entity_col": entity_ids[0] if entity_ids else (cat_fields[0] if cat_fields else "item"),
            "entity_count_label": "Total Stock Items",
            "secondary_metric": primary if primary else None,
            "secondary_metric_label": f"Average {primary}" if primary else None,
            "secondary_metric_op": "mean" if primary else None,
            "secondary_metric_type": "generic",
            "status_col": status_fields[0] if status_fields else None,
            "status_metric_label": "Item Available Ratio" if status_fields else None,
            "status_healthy_regex": "Available|In Stock|Active",
            "status_unhealthy_regex": "Out of Stock|Discontinued|Backordered",
            "chart_title": "Stock Quantity History"
        }
    elif domain == "marketing":
        spend = next((m for m in num_metrics if "spend" in m.lower() or "cost" in m.lower() or "budget" in m.lower()), None)
        conv = next((m for m in num_metrics if "conversion" in m.lower() or "lead" in m.lower() or "click" in m.lower()), (num_metrics[0] if num_metrics else None))
        bus_term = {
            "dashboard_title": "Marketing ROI & Campaign Dashboard",
            "primary_metric": spend if spend else (conv if conv else "ad_spend"),
            "primary_metric_label": f"Total {spend}" if spend else "Total Ad Performance",
            "primary_metric_op": "sum",
            "primary_metric_type": "currency" if spend else "count",
            "entity_col": entity_ids[0] if entity_ids else (cat_fields[0] if cat_fields else "campaign"),
            "entity_count_label": "Total Campaigns",
            "secondary_metric": conv if conv else None,
            "secondary_metric_label": f"Total {conv}" if conv else None,
            "secondary_metric_op": "sum" if conv else None,
            "secondary_metric_type": "count",
            "status_col": status_fields[0] if status_fields else None,
            "status_metric_label": "Active Campaign Ratio" if status_fields else None,
            "status_healthy_regex": "Active|Live|Approved",
            "status_unhealthy_regex": "Paused|Stopped|Ended|Rejected",
            "chart_title": "Campaign Spend & Conversion Trend"
        }
    elif domain == "CRM":
        value = next((m for m in num_metrics if "value" in m.lower() or "amount" in m.lower() or "size" in m.lower()), (num_metrics[0] if num_metrics else None))
        bus_term = {
            "dashboard_title": "Sales Pipeline & CRM Hub",
            "primary_metric": value if value else "deals",
            "primary_metric_label": f"Total Deal {value}" if value else "Total Deals Count",
            "primary_metric_op": "sum" if value else "count",
            "primary_metric_type": "currency" if value else "count",
            "entity_col": entity_ids[0] if entity_ids else (cat_fields[0] if cat_fields else "lead"),
            "entity_count_label": "Total Leads",
            "secondary_metric": value if value else None,
            "secondary_metric_label": f"Avg Deal {value}" if value else None,
            "secondary_metric_op": "mean" if value else None,
            "secondary_metric_type": "currency" if value else None,
            "status_col": status_fields[0] if status_fields else None,
            "status_metric_label": "Deal Conversion Win Rate" if status_fields else None,
            "status_healthy_regex": "Won|Qualified|Closed",
            "status_unhealthy_regex": "Lost|Dead|Unqualified",
            "chart_title": "Deal Pipeline Growth"
        }
    elif domain == "banking":
        bal = next((m for m in num_metrics if "balance" in m.lower() or "amount" in m.lower() or "deposit" in m.lower()), (num_metrics[0] if num_metrics else None))
        bus_term = {
            "dashboard_title": "Banking & Accounts Operating Center",
            "primary_metric": bal if bal else "deposits",
            "primary_metric_label": f"Total {bal}" if bal else "Total Deposits",
            "primary_metric_op": "sum",
            "primary_metric_type": "currency",
            "entity_col": entity_ids[0] if entity_ids else (cat_fields[0] if cat_fields else "account"),
            "entity_count_label": "Total Accounts",
            "secondary_metric": bal if bal else None,
            "secondary_metric_label": f"Average {bal}" if bal else None,
            "secondary_metric_op": "mean" if bal else None,
            "secondary_metric_type": "currency" if bal else None,
            "status_col": status_fields[0] if status_fields else None,
            "status_metric_label": "Account Active Ratio" if status_fields else None,
            "status_healthy_regex": "Active|Approved|Open|Success",
            "status_unhealthy_regex": "Closed|Suspended|Inactive",
            "chart_title": "Asset Balance Progress"
        }
    elif domain == "finance":
        rev = next((m for m in num_metrics if "revenue" in m.lower() or "income" in m.lower() or "amount" in m.lower()), (num_metrics[0] if num_metrics else None))
        profit = next((m for m in num_metrics if "profit" in m.lower() or "margin" in m.lower() or "net" in m.lower()), (num_metrics[1] if len(num_metrics) > 1 else None))
        bus_term = {
            "dashboard_title": "Corporate Finance & Treasury Suite",
            "primary_metric": rev if rev else "finance_value",
            "primary_metric_label": f"Total {rev}" if rev else "Total Financial Value",
            "primary_metric_op": "sum",
            "primary_metric_type": "currency",
            "entity_col": entity_ids[0] if entity_ids else (cat_fields[0] if cat_fields else "transaction"),
            "entity_count_label": "Total Transactions",
            "secondary_metric": profit if profit else (rev if rev else None),
            "secondary_metric_label": f"Total {profit}" if profit else (f"Average {rev}" if rev else None),
            "secondary_metric_op": "sum" if profit else ("mean" if rev else None),
            "secondary_metric_type": "currency" if profit or rev else None,
            "status_col": status_fields[0] if status_fields else None,
            "status_metric_label": "Clearance Success Rate" if status_fields else None,
            "status_healthy_regex": "Paid|Approved|Settled|Cleared|Success",
            "status_unhealthy_regex": "Unpaid|Overdue|Void|Failed",
            "chart_title": "Cashflow History"
        }
    elif domain == "sales":
        rev = next((m for m in num_metrics if "revenue" in m.lower() or "sales" in m.lower() or "amount" in m.lower() or "order_value" in m.lower()), (num_metrics[0] if num_metrics else None))
        profit = next((m for m in num_metrics if "profit" in m.lower() or "discount" in m.lower()), (num_metrics[1] if len(num_metrics) > 1 else None))
        bus_term = {
            "dashboard_title": "Sales & Revenue Intelligence Suite",
            "primary_metric": rev if rev else "sales_value",
            "primary_metric_label": f"Total {rev}" if rev else "Total Revenue",
            "primary_metric_op": "sum",
            "primary_metric_type": "currency",
            "entity_col": next((c for c in entity_ids if "customer" in c.lower() or "user" in c.lower()), (entity_ids[0] if entity_ids else "customer")),
            "entity_count_label": "Total Customers",
            "secondary_metric": profit if profit else (rev if rev else None),
            "secondary_metric_label": f"Total {profit}" if profit else (f"Average {rev}" if rev else None),
            "secondary_metric_op": "sum" if profit else ("mean" if rev else None),
            "secondary_metric_type": "currency" if profit or rev else None,
            "status_col": status_fields[0] if status_fields else None,
            "status_metric_label": "Order Fullfillment Rate" if status_fields else None,
            "status_healthy_regex": "Completed|Shipped|Delivered|Success",
            "status_unhealthy_regex": "Cancelled|Returned|Refunded|Failed",
            "chart_title": "Revenue Performance Trend"
        }
    else: # Generic
        primary = num_metrics[0] if num_metrics else None
        secondary = num_metrics[1] if len(num_metrics) > 1 else (num_metrics[0] if num_metrics else None)
        bus_term = {
            "dashboard_title": "Enterprise Intelligence Platform",
            "primary_metric": primary if primary else "records",
            "primary_metric_label": f"Total {primary}" if primary else "Total Records",
            "primary_metric_op": "sum" if primary else "count",
            "primary_metric_type": "generic" if primary else "count",
            "entity_col": entity_ids[0] if entity_ids else (cat_fields[0] if cat_fields else "item"),
            "entity_count_label": "Total Items",
            "secondary_metric": secondary if secondary else None,
            "secondary_metric_label": f"Average {secondary}" if secondary else None,
            "secondary_metric_op": "mean" if secondary else None,
            "secondary_metric_type": "generic",
            "status_col": status_fields[0] if status_fields else None,
            "status_metric_label": "Success Rate" if status_fields else None,
            "status_healthy_regex": "Success|Active|Approved|Completed",
            "status_unhealthy_regex": "Failed|Inactive|Cancelled|Rejected",
            "chart_title": "Metric Analytics History"
        }
        
    validate_and_sanitize_business_terminology(df, domain, bus_term)
    return domain, {
        "domain": domain,
        "semantic_dictionary": {
            "date_columns": date_cols,
            "numeric_metrics": num_metrics,
            "categorical_fields": cat_fields,
            "entity_identifiers": entity_ids,
            "status_fields": status_fields,
            "geographic_fields": geo_fields
        },
        "business_terminology": bus_term
    }

def classify_dataset_and_build_dictionary(df: pd.DataFrame, filename: str) -> tuple[str, dict]:
    """
    Main entrypoint to classify the dataset and build a semantic data dictionary.
    First tries to use Groq LLM to yield high fidelity results. Falls back to
    rule-based parser if any error occurs.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        logging.warning("No GROQ_API_KEY found, falling back to heuristic semantic dictionary.")
        return fallback_classify(df, filename)
        
    try:
        # Sample metadata
        columns = [{"name": str(c), "type": str(df[c].dtype)} for c in df.columns]
        # Get 3 sample rows
        sample_df = df.head(3).astype(str)
        sample_rows = sample_df.to_dict(orient="records")
        
        prompt = f"""You are a senior data architect. Analyze this uploaded dataset file: '{filename}'
Columns and types: {json.dumps(columns)}
Sample data rows (up to 3): {json.dumps(sample_rows)}

Perform two tasks:
1. Detect the dataset business domain (MUST be exactly one of: banking, sales, HR, healthcare, inventory, marketing, CRM, finance, generic).
2. Build a semantic data dictionary classifying all columns into:
   - Date columns (e.g. order date, hired date, timestamps)
   - Numeric metrics (numeric fields to aggregate, like sales, balance, salary, count, click, spend. DO NOT include ID columns or phone numbers or ZIP codes here!)
   - Categorical fields (categories, types, names, product groups)
   - Entity identifiers (IDs, keys, codes, patient number, employee ID)
   - Status fields (stage, status, active/inactive indicator)
   - Geographic fields (country, state, region, city, zip)
   
3. Formulate dynamic business terminology mapping to dynamically adapt a business dashboard's titles, metrics, and charts:
   - dashboard_title: Specific, premium dashboard title (e.g., 'Workforce Operations Hub' for HR, 'Clinical Admissions Hub' for Healthcare, etc.)
   - primary_metric: The column name representing the absolute primary business metric in this dataset (e.g. Sales, Salary, Balance, Spend, Stock Level). Use a real column name. If no numeric column is found, use 'records' (as row count).
   - primary_metric_label: Specific premium business label for the primary metric sum (e.g. 'Total Revenue' or 'Workforce Spend' or 'Asset Deposits' or 'Stock Quantity').
   - primary_metric_op: The pandas aggregate operation for the primary metric ('sum', 'mean', 'count', 'nunique').
   - primary_metric_type: 'currency', 'count', 'percent', or 'generic'.
   - entity_col: The primary entity column to count (e.g. Customer ID, Employee ID, Patient ID, Product SKU).
   - entity_count_label: Dynamic label for entity count (e.g. 'Total Patients' or 'Active Employees' or 'Total Accounts').
   - secondary_metric: Column name representing a secondary metric (e.g., profit, salary, stay duration, click count).
   - secondary_metric_label: Label for the secondary metric (e.g. 'Average Salary' or 'Cost per Acquisition' or 'Ad clicks').
   - secondary_metric_op: Aggregation operation ('mean', 'sum', 'count', 'nunique').
   - secondary_metric_type: 'currency', 'count', 'percent', or 'generic'.
   - status_col: The status/stage column name if any.
   - status_metric_label: The friendly business label for the status success percentage (e.g. 'Lead Conversion Win Rate' or 'Employee Retention Rate' or 'Treatment Completion Rate').
   - status_healthy_regex: A Python regular expression matching positive/healthy states (e.g., 'won|active|discharged|completed|approved|paid').
   - status_unhealthy_regex: A Python regular expression matching negative/unhealthy states (e.g., 'lost|terminated|churned|inactive|overdue|failed').
   - chart_title: Specific title for the monthly trend chart (e.g., 'Workforce Size Trend', 'Monthly Patient Flow', 'Revenue Performance Trend').

CRITICAL RULES:
- Never use generic labels like Revenue, Customers, Deal Size unless those concepts explicitly exist in the dataset columns.
- Use dataset-specific business terminology throughout the UI.
- Use only actual columns present in the dataset columns list. Do not invent columns. If a metric/concept is missing, replace it with a more appropriate metric derived from the data columns.
- Return ONLY a valid JSON object with the keys "domain", "semantic_dictionary", and "business_terminology". Do not include markdown code formatting backticks in your reply.

JSON Response format:
{{
  "domain": "sales",
  "semantic_dictionary": {{
    "date_columns": ["Order Date"],
    "numeric_metrics": ["Sales", "Profit", "Quantity"],
    "categorical_fields": ["Category", "Sub-Category"],
    "entity_identifiers": ["Customer ID", "Order ID"],
    "status_fields": ["Order Status"],
    "geographic_fields": ["Country", "City"]
  }},
  "business_terminology": {{
    "dashboard_title": "Sales Performance Intelligence",
    "primary_metric": "Sales",
    "primary_metric_label": "Total Sales Revenue",
    "primary_metric_op": "sum",
    "primary_metric_type": "currency",
    "entity_col": "Customer ID",
    "entity_count_label": "Total Active Customers",
    "secondary_metric": "Profit",
    "secondary_metric_label": "Total Net Profit",
    "secondary_metric_op": "sum",
    "secondary_metric_type": "currency",
    "status_col": "Order Status",
    "status_metric_label": "Order Fullfillment Rate",
    "status_healthy_regex": "Delivered|Shipped|Completed",
    "status_unhealthy_regex": "Cancelled|Returned",
    "chart_title": "Monthly Sales Performance"
  }}
}}
"""
        res = completion(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        content = res.choices[0].message.content.strip()
        # strip markdown formatting just in case
        if content.startswith("```"):
            m = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
            if m:
                content = m.group(1).strip()
        
        parsed = json.loads(content)
        domain = parsed.get("domain", "generic")
        # Validate domain list
        allowed_domains = ["banking", "sales", "HR", "healthcare", "inventory", "marketing", "CRM", "finance", "generic"]
        # case insensitive match
        domain_match = next((d for d in allowed_domains if d.lower() == str(domain).lower()), None)
        if domain_match:
            domain = domain_match
        else:
            domain = "generic"
            
        semantic_dictionary = parsed.get("semantic_dictionary", {})
        business_terminology = parsed.get("business_terminology", {})
        
        # Verify columns exist in the dataframe to prevent LLM hallucinations
        cols_set = set(df.columns)
        for k in ["date_columns", "numeric_metrics", "categorical_fields", "entity_identifiers", "status_fields", "geographic_fields"]:
            if k in semantic_dictionary:
                semantic_dictionary[k] = [c for c in semantic_dictionary[k] if c in cols_set]
                
        # Verify business terms map to real columns
        for k in ["primary_metric", "secondary_metric", "entity_col", "status_col"]:
            val = business_terminology.get(k)
            if val and val not in cols_set:
                business_terminology[k] = None
                
        # Fill missing values from fallback to ensure dictionary is 100% complete
        _, fallback_dict = fallback_classify(df, filename)
        
        # Merge dictionary lists
        for k in ["date_columns", "numeric_metrics", "categorical_fields", "entity_identifiers", "status_fields", "geographic_fields"]:
            if not semantic_dictionary.get(k):
                semantic_dictionary[k] = fallback_dict["semantic_dictionary"].get(k, [])
                
        # Merge business terms
        for k, v in fallback_dict["business_terminology"].items():
            if not business_terminology.get(k):
                business_terminology[k] = v
                
        # Double check status health fallback values
        if not business_terminology.get("status_healthy_regex"):
            business_terminology["status_healthy_regex"] = "won|active|discharged|completed|approved|paid"
        if not business_terminology.get("status_unhealthy_regex"):
            business_terminology["status_unhealthy_regex"] = "lost|terminated|churned|inactive|overdue|failed"
            
        validate_and_sanitize_business_terminology(df, domain, business_terminology)
        return domain, {
            "domain": domain,
            "semantic_dictionary": semantic_dictionary,
            "business_terminology": business_terminology
        }
    except Exception as e:
        logging.error(f"LLM Classification failed: {e}. Falling back to rule-based classification.")
        return fallback_classify(df, filename)
