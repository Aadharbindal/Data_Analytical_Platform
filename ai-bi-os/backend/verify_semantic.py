import os
import sys
import pandas as pd
import json

# Ensure backend app is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.semantic_classification import classify_dataset_and_build_dictionary, fallback_classify
from app.services.stats_service import compute_kpis

# Create a sample HR dataset
hr_data = {
    "Employee ID": ["EMP001", "EMP002", "EMP003", "EMP004"],
    "Staff Name": ["Alice", "Bob", "Charlie", "David"],
    "Department": ["Sales", "Engineering", "HR", "Marketing"],
    "Hired Date": ["2021-01-15", "2022-05-10", "2020-03-01", "2023-08-20"],
    "Monthly Salary": [5000, 7000, 4500, 6000],
    "Employment Status": ["Active", "Active", "Terminated", "Active"],
    "Office Country": ["USA", "Canada", "USA", "UK"]
}
df_hr = pd.DataFrame(hr_data)

# Create a sample Sales dataset
sales_data = {
    "Order ID": ["ORD100", "ORD101", "ORD102", "ORD103"],
    "Customer Code": ["CUST90", "CUST91", "CUST92", "CUST93"],
    "Deal Size Amount": [150.00, 2300.00, 45.50, 670.00],
    "Order Date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
    "Order Status": ["Completed", "Shipped", "Cancelled", "Completed"],
    "Product Category": ["Office", "Tech", "Office", "Furniture"],
    "Sales Rep State": ["NY", "CA", "TX", "WA"]
}
df_sales = pd.DataFrame(sales_data)

# Create a sample Health dataset
health_data = {
    "Patient Identifier": ["PAT01", "PAT02", "PAT03", "PAT04"],
    "Patient Age": [34, 45, 29, 62],
    "Admission Timestamp": ["2026-07-01 10:00", "2026-07-02 11:30", "2026-07-02 14:00", "2026-07-03 09:15"],
    "Clinical Diagnosis": ["Flu", "Appendicitis", "Migraine", "Pneumonia"],
    "Medical Charges Cost": [1200.00, 8500.00, 450.00, 6200.00],
    "Discharge Status": ["Discharged", "Completed", "Active", "Completed"],
    "Hospital Zipcode": ["10001", "90210", "75001", "98101"]
}
df_health = pd.DataFrame(health_data)

print("--------------------------------------------------")
print("1. RUNNING RULE-BASED FALLBACK CLASSIFIER")
print("--------------------------------------------------")

for name, df in [("hr_data.csv", df_hr), ("sales_data.csv", df_sales), ("patient_admissions.csv", df_health)]:
    domain, res = fallback_classify(df, name)
    print(f"\nFile: {name} -> INFERRED DOMAIN: {domain}")
    print("Semantic Dictionary:")
    print(json.dumps(res["semantic_dictionary"], indent=2))
    print("Business Terminology:")
    print(json.dumps(res["business_terminology"], indent=2))

print("--------------------------------------------------")
print("2. RUNNING FULL CLASSIFIER WITH LLM")
print("--------------------------------------------------")

# Let's test the main entry point (will run LLM if GROQ_API_KEY is configured, fallback otherwise)
domain_hr, res_hr = classify_dataset_and_build_dictionary(df_hr, "workforce_headcount_tracker.csv")
print(f"workforce_headcount_tracker.csv -> Inferred Domain: {domain_hr}")
print(json.dumps(res_hr, indent=2))

print("--------------------------------------------------")
print("3. RUNNING STATS SERVICE / KPI COMPILATION")
print("--------------------------------------------------")

kpis_hr = compute_kpis(df_hr, res_hr)
print("Computed HR KPIs:")
print(json.dumps(kpis_hr["kpis"], indent=2))

print("\nComputed HR Chart Data (sample 3):")
print(json.dumps(kpis_hr["chart_data"][:3], indent=2))

domain_sales, res_sales = classify_dataset_and_build_dictionary(df_sales, "customer_sales_performance.csv")
kpis_sales = compute_kpis(df_sales, res_sales)
print("\nComputed Sales KPIs:")
print(json.dumps(kpis_sales["kpis"], indent=2))

print("\nVERIFICATION COMPLETED SUCCESSFULLY.")
