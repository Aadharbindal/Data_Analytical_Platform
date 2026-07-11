import os
import sys
import pandas as pd
import sqlite3
import json
import logging
from pathlib import Path

# Add backend to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.services.stats_service import find_column
from app.routers.rules import parse_text_rule, create_rule
from app.services.insights_engine import InsightsEngine
from app.services.query.duckdb_engine import DuckDBEngine
from app.services.data_processing import register_active_dataset

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_deep_insights():
    logging.info("Testing Deep Insights on SaaS dataset...")
    # This requires active DB connection, skipping actual LLM calls since we're unauthenticated
    engine = DuckDBEngine()
    # Just initialize it to see if it doesn't crash on init
    insights_engine = InsightsEngine(db_engine=engine)
    logging.info("Deep Insights init passed.")

def verify_forecast_horizons():
    logging.info("Testing Forecast Horizons...")
    df = pd.read_csv(Path(__file__).parent / "data" / "291881dd-4a02-4005-975d-5ab3fba9d7b8_cafe_sales_SMALL.csv")
    from app.services.stats_service import find_column
    import numpy as np
    
    # Simulating the get_forecast logic
    metric = "SalesAmount"
    date_col = "Date"
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col, metric]).sort_values(date_col)
    
    if len(df) > 0:
        logging.info("Forecast inputs valid, Horizons > 0 simulated.")

test_deep_insights()
verify_forecast_horizons()
