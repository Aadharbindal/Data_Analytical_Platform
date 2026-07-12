import asyncio
from app.services.insights_engine import DeepInsightsEngine
from app.services.query.duckdb_engine import DuckDBEngine
import os
from dotenv import load_dotenv

import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()

def main():
    datasets = [
        "data/0cddbdbc-ba08-4b45-a582-c792e8f72b9e_electronics_sales_BIG.csv",
        "data/6c7d6c39-4a46-4a54-8841-6bef83a66eca_food_delivery_FINAL_TEST.csv",
        "data/bdf0e003-a786-460d-852a-47fd9e248cae_software_licenses_FINAL_VERIFY.csv",
        "data/ccaecda4-2c8b-4757-b693-1ea8e5296e76_bank_statement_FINAL.csv",
        "data/45a1b577-96de-4c8f-8d15-05d0af29d203_saas_subscriptions_TEST.csv"
    ]
    
    for filepath in datasets:
        print(f"\n==========================================")
        print(f"Testing: {filepath}")
        db_engine = DuckDBEngine()
        db_engine.register_dataset("active_dataset", filepath, format="csv")
        engine = DeepInsightsEngine(db_engine)
        
        insights = engine.generate_insights("test_user", "test_dataset")
        print(f"Insights generated for {filepath}: {len(insights)}")
        if not insights:
            print(f"Empty insights array returned for {filepath}!")
        else:
            print("First insight sample:")
            print(insights[0])
            
        db_engine.close()
        
        import time
        print("Sleeping for 60 seconds to avoid TPM rate limit...")
        time.sleep(60)

if __name__ == "__main__":
    main()

