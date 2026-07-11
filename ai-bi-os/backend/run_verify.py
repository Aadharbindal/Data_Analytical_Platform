import asyncio
from app.services.insights_engine import DeepInsightsEngine
from app.services.query.duckdb_engine import DuckDBEngine
import os
from dotenv import load_dotenv
import logging
import json

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()

def main():
    datasets = [
        "data/a8c0266f-b174-438b-965d-c9e39f7f0609_wallet_transactions_FRESH.csv",
        "data/0cddbdbc-ba08-4b45-a582-c792e8f72b9e_electronics_sales_BIG.csv",
        "data/291881dd-4a02-4005-975d-5ab3fba9d7b8_cafe_sales_SMALL.csv"
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
            for ins in insights:
                print(f"Insight ID: {ins.get('id')}")
                print(f"Title: {ins.get('title')}")
                print(f"Category: {ins.get('category')}")
                print(f"Desc: {ins.get('description')}")
                print(f"Impact: {ins.get('impact')}")
                print(f"SQL: {ins.get('sql')}")
                print("-" * 20)
                
                # Check for speculative terms
                text = f"{ins.get('title')} {ins.get('description')}".lower()
                bad_words = ["might", "could", "anticipate", "projected", "likely to", "expected to", "predicted", "prediction", "probability of", "likelihood of", "forecast to", "chance of"]
                for w in bad_words:
                    if w in text:
                        print(f"WARNING: Speculative term '{w}' found in insight!")
                        
        db_engine.close()

if __name__ == "__main__":
    main()
