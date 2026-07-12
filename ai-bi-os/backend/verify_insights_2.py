import os
from dotenv import load_dotenv
from app.services.insights_engine import DeepInsightsEngine
from app.services.query.duckdb_engine import DuckDBEngine
import time
import json
import logging

logging.basicConfig(level=logging.WARNING)

load_dotenv()

def run_test(filepath, num_runs=1):
    db_engine = DuckDBEngine()
    db_engine.register_dataset("active_dataset", filepath, format="csv")
    engine = DeepInsightsEngine(db_engine)
    
    all_insights = []
    for i in range(num_runs):
        print(f"\n--- Run {i+1} for {filepath} ---")
        try:
            insights = engine.generate_insights("test_user", "test_dataset")
            for ins in insights:
                print(f"Title: {ins.get('title')}")
                print(f"Desc: {ins.get('description')}")
                print(f"Category: {ins.get('category')}")
                print(f"SQL: {ins.get('sql')}")
                print("-")
            all_insights.extend(insights)
        except Exception as e:
            print(f"Failed run {i+1}: {e}")
            
    db_engine.close()
    return all_insights

def main():
    print("VERIFICATION: Testing Wallet Transactions and 2 other datasets")
    
    wallet_csv = "data/a8c0266f-b174-438b-965d-c9e39f7f0609_wallet_transactions_FRESH.csv"
    other_1 = "data/0cddbdbc-ba08-4b45-a582-c792e8f72b9e_electronics_sales_BIG.csv"
    other_2 = "data/291881dd-4a02-4005-975d-5ab3fba9d7b8_cafe_sales_SMALL.csv"
    
    print(f"\nTesting: {wallet_csv}")
    run_test(wallet_csv, 1)
    
    print(f"\nTesting: {other_1}")
    run_test(other_1, 1)
    
    print(f"\nTesting: {other_2}")
    run_test(other_2, 1)

if __name__ == '__main__':
    main()
