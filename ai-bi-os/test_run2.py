import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging for our script to capture output
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s: %(message)s')
# Patch sys.stdout to handle unicode on windows
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr:
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv("backend/.env")
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.query.duckdb_engine import DuckDBEngine
from app.services.insights_engine import DeepInsightsEngine
import json

def test_dataset(filename):
    print(f"\n\n================ TEST DATASET: {filename} ================\n\n")
    db_engine = DuckDBEngine()
    db_engine.register_dataset("active_dataset", os.path.join("backend/data", filename), format="csv")
    
    engine = DeepInsightsEngine(db_engine)
    
    import app.services.insights_engine
    
    # We will temporarily patch `completion` to print the kwargs so we can see the exact input
    original_completion = app.services.insights_engine.completion
    def mock_completion(*args, **kwargs):
        print("====== COMPLETION CALLED ======")
        print("MESSAGES:", json.dumps(kwargs.get("messages"), indent=2))
        res = original_completion(*args, **kwargs)
        print("RESPONSE CONTENT:", repr(res.choices[0].message.content))
        print("RESPONSE FINISH REASON:", res.choices[0].finish_reason)
        return res
        
    app.services.insights_engine.completion = mock_completion
    
    insights = engine.generate_insights("test_user_1", "test_dataset_1")
    db_engine.close()
    
    print("\nFINAL INSIGHTS:")
    for ins in insights:
        print(ins.get('title'), ":", ins.get('description'))
        
if __name__ == "__main__":
    test_dataset("ccaecda4-2c8b-4757-b693-1ea8e5296e76_bank_statement_FINAL.csv")
