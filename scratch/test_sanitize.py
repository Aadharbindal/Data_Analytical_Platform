import pandas as pd
import sys
import re

sys.path.append(r'c:\Users\user\Documents\Data_Analytics\ai-bi-os\backend')
from app.services.semantic_classification import validate_and_sanitize_business_terminology

df = pd.read_csv(r'c:\Users\user\Documents\Data_Analytics\ai-bi-os\backend\data\066b3ad8-80fd-444e-b422-0bd845c793f3_upi_bank_statement_TEST_NEW.csv')
bus_term = {
  "dashboard_title": "Financial Transaction Hub",
  "primary_metric": "Amount",
  "primary_metric_label": "Total Transaction Value",
  "primary_metric_op": "sum",
  "primary_metric_type": "currency",
  "entity_col": "UPI_ID",
  "entity_count_label": "Total Transactions",
  "secondary_metric": "Amount",
  "secondary_metric_label": "Average Transaction Value",
  "secondary_metric_op": "mean",
  "secondary_metric_type": "currency",
  "status_col": "TxnStatus",
  "status_metric_label": "Transaction Success Rate",
  "status_healthy_regex": "Success",
  "status_unhealthy_regex": "Failed",
  "chart_title": "Monthly Transaction Trend"
}

print("Before:", bus_term["entity_col"], bus_term["entity_count_label"])
validate_and_sanitize_business_terminology(df, "finance", bus_term)
print("After:", bus_term["entity_col"], bus_term["entity_count_label"])

# Let's check regex searches on column names
for c in df.columns:
    col_lower = str(c).lower()
    match = re.search(r'\b(utr|ref|reference|txn_id|txnid|order_id|invoice_id|trans_id)\b', col_lower)
    print(f"Col: {c}, Lower: {col_lower}, Match: {match}")
