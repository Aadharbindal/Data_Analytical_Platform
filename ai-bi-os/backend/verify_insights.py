import os
from dotenv import load_dotenv
from app.services.insights_engine import DeepInsightsEngine
from app.services.query.duckdb_engine import DuckDBEngine
import time
import json
import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")

load_dotenv()

def run_test(filepath, num_runs=1):
    db_engine = DuckDBEngine()
    db_engine.register_dataset("active_dataset", filepath, format="csv")
    engine = DeepInsightsEngine(db_engine)
    
    all_insights = []
    for i in range(num_runs):
        print(f"\n--- Run {i+1} for {filepath} ---")
        insights = engine.generate_insights("test_user", "test_dataset")
        for ins in insights:
            print(f"Title: {ins.get('title')}")
            print(f"Desc: {ins.get('description')}")
            print(f"Impact: {ins.get('impact')}")
            print("-")
        all_insights.extend(insights)
        if i < num_runs - 1:
            time.sleep(5)
            
    db_engine.close()
    return all_insights

def main():
    target_csv = "data/52026dc1-ebdb-45dd-9c76-77b107caf3e7_corporate_bank_statement_FINAL.csv"
    print("VERIFICATION 1 & 2: Running multiple times on corporate_bank_statement_FINAL.csv")
    insights = run_test(target_csv, num_runs=3)
    
    finance_found = False
    salary_found = False
    
    for ins in insights:
        title_desc = (ins.get('title', '') + " " + ins.get('description', '')).lower()
        if "finance" in title_desc and "4,096" in title_desc:
            finance_found = True
        if "finance" in title_desc and "4096" in title_desc:
            finance_found = True
        if "salary" in title_desc and "interest" in title_desc:
            salary_found = True
            
    print(f"\nFinance Dept insight found: {finance_found}")
    print(f"Salary vs Interest insight found: {salary_found}")
    
    print("\nVERIFICATION 3: Testing 2 other datasets")
    other_1 = "data/0cddbdbc-ba08-4b45-a582-c792e8f72b9e_electronics_sales_BIG.csv"
    other_2 = "data/291881dd-4a02-4005-975d-5ab3fba9d7b8_cafe_sales_SMALL.csv"
    
    print(f"\nTesting: {other_1}")
    run_test(other_1, 1)
    
    print(f"\nTesting: {other_2}")
    run_test(other_2, 1)

if __name__ == '__main__':
    main()
