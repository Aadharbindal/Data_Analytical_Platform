import asyncio
from app.services.insights_engine import DeepInsightsEngine
from app.services.query.duckdb_engine import DuckDBEngine
import os
from dotenv import load_dotenv
load_dotenv()
import logging
logging.basicConfig(level=logging.INFO)
db = DuckDBEngine()
db.register_dataset('active_dataset', 'data/45a1b577-96de-4c8f-8d15-05d0af29d203_saas_subscriptions_TEST.csv', format='csv')
engine = DeepInsightsEngine(db)
insights = engine.generate_insights('test', 'test')
print('Result:', insights)
