import sqlite3
import json
import sys
import os

sys.path.append(r'c:\Users\user\Documents\Data_Analytics\ai-bi-os\backend')
from app.core.config import DB_PATH
print("DB_PATH:", DB_PATH)

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# Get table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

try:
    cursor.execute("SELECT id, name, domain, semantic_dict FROM datasets")
    rows = cursor.fetchall()
    for row in rows:
        print(f"\nDataset ID: {row[0]}, Name: {row[1]}, Domain: {row[2]}")
        try:
            sem = json.loads(row[3])
            print("Business Terminology:")
            print(json.dumps(sem.get("business_terminology", {}), indent=2))
        except Exception as e:
            print("Error parsing semantic dict:", e)
except Exception as e:
    print("Error querying datasets:", e)
