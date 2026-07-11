import os
import sys
import logging
import codecs
from dotenv import load_dotenv

# Silence the huge amount of logs, we just want to see the final insights or the fallback
logging.basicConfig(level=logging.ERROR, stream=sys.stdout, format='%(levelname)s: %(message)s')
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr:
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv("backend/.env")
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.query.duckdb_engine import DuckDBEngine
from app.services.insights_engine import DeepInsightsEngine

def run_stress_test():
    targets = [
        "electronics_sales_BIG.csv",
        "food_delivery_FINAL_TEST.csv",
        "software_licenses_FINAL_VERIFY.csv",
        "bank_statement_FINAL.csv",
        "saas_subscriptions_TEST.csv"
    ]
    
    data_dir = "backend/data"
    all_files = os.listdir(data_dir)
    
    for target in targets:
        import time
        time.sleep(15)
        # Find the actual file name
        actual_file = next((f for f in all_files if target in f), None)
        if not actual_file:
            print(f"[{target}] NOT FOUND in {data_dir}")
            continue
            
        print(f"\n=======================================================")
        print(f" TESTING: {target}")
        print(f"=======================================================")
        
        db_engine = DuckDBEngine()
        db_engine.register_dataset("active_dataset", os.path.join(data_dir, actual_file), format="csv")
        
        engine = DeepInsightsEngine(db_engine)
        try:
            insights = engine.generate_insights("stress_test_user", "test_dataset")
        except Exception as e:
            print(f"Exception during generate_insights: {e}")
            insights = [{"title": "Z-Score Fallback", "sql": ""}]
            
        db_engine.close()
        
        fallback = False
        if any("Z-Score Fallback" in ins.get('title', '') for ins in insights):
            fallback = True
            
        if fallback:
            print(f"❌ {target} FAILED - fell back to Z-score")
        else:
            print(f"✅ {target} PASSED - generated {len(insights)} insights")
            for i, ins in enumerate(insights):
                print(f"  Insight {i+1}: {ins.get('title')}")
                # print(f"    SQL: {ins.get('sql')}")

if __name__ == "__main__":
    run_stress_test()
