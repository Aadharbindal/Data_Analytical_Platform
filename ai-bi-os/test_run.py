import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging for our script to capture output
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s: %(message)s')

load_dotenv("backend/.env")

# Must set Python path so we can import app modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.query.duckdb_engine import DuckDBEngine
from app.services.insights_engine import DeepInsightsEngine
from app.core.config import DB_PATH

def test_dataset(filename):
    print(f"\n\n================ TEST DATASET: {filename} ================\n\n")
    db_engine = DuckDBEngine()
    db_engine.register_dataset("active_dataset", os.path.join("backend/data", filename), format="csv")
    
    engine = DeepInsightsEngine(db_engine)
    insights = engine.generate_insights("test_user_1", "test_dataset_1")
    db_engine.close()
    
    print("\nFINAL INSIGHTS:")
    for ins in insights:
        print(ins.get('title'), ":", ins.get('description'))
        
if __name__ == "__main__":
    test_dataset("52026dc1-ebdb-45dd-9c76-77b107caf3e7_corporate_bank_statement_FINAL.csv")
    test_dataset("a0113953-1bcd-45d5-85ac-8c02b3a92cce_bank_statement_FINAL_TEST.csv")
    test_dataset("ccaecda4-2c8b-4757-b693-1ea8e5296e76_bank_statement_FINAL.csv")
