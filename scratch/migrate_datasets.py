import sqlite3
import json
import os
import sys
import pandas as pd

sys.path.append(r'c:\Users\user\Documents\Data_Analytics\ai-bi-os\backend')
from app.core.config import DB_PATH
from app.services.data_processing import get_dataset_path
from app.services.semantic_classification import validate_and_sanitize_business_terminology

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

cursor.execute("SELECT id, name, domain, semantic_dict, filepath FROM datasets")
rows = cursor.fetchall()

for row in rows:
    dataset_id, name, domain, semantic_dict_json, filepath = row
    if not semantic_dict_json or not filepath:
        continue
    
    disk_path = get_dataset_path(filepath)
    if not os.path.exists(disk_path):
        print(f"File not found: {disk_path}")
        continue
        
    try:
        df = pd.read_csv(disk_path)
        semantic_dict = json.loads(semantic_dict_json)
        bus_term = semantic_dict.get("business_terminology", {})
        
        print(f"\nDataset: {name}")
        print(f"  Before: entity_col={bus_term.get('entity_col')}, label={bus_term.get('entity_count_label')}")
        
        # Run sanitization
        validate_and_sanitize_business_terminology(df, domain, bus_term)
        
        print(f"  After: entity_col={bus_term.get('entity_col')}, label={bus_term.get('entity_count_label')}")
        
        # Save back
        semantic_dict["business_terminology"] = bus_term
        cursor.execute("UPDATE datasets SET semantic_dict = ? WHERE id = ?", (json.dumps(semantic_dict), dataset_id))
        conn.commit()
        print("  Database updated successfully.")
        
    except Exception as e:
        print(f"  Error processing dataset {name}: {e}")

conn.close()
