import os
import pandas as pd
import uuid
import json
from datetime import datetime
import sqlite3

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "datamind.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            id TEXT PRIMARY KEY,
            name TEXT,
            status TEXT,
            created_at TEXT,
            latest_version JSON,
            filepath TEXT,
            columns JSON
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS catalog (
            id TEXT PRIMARY KEY,
            name TEXT,
            domain TEXT,
            description TEXT,
            owner TEXT,
            tags JSON
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_dataset (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            dataset_id TEXT,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_dataset(file_content: bytes, filename: str):
    dataset_id = str(uuid.uuid4())
    filepath = os.path.join(DATA_DIR, f"{dataset_id}_{filename}")
    with open(filepath, "wb") as f:
        f.write(file_content)
    
    # Try parsing
    if filename.endswith(".csv"):
        df = pd.read_csv(filepath)
    elif filename.endswith(".xlsx"):
        df = pd.read_excel(filepath)
    else:
        df = pd.read_csv(filepath) # fallback
        
    row_count = len(df)
    col_count = len(df.columns)
    
    # Create profile
    columns = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        null_count = int(df[col].isnull().sum())
        col_info = {"name": col, "type": dtype, "null_count": null_count}
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info["mean"] = float(df[col].mean()) if not pd.isna(df[col].mean()) else 0
            col_info["min"] = float(df[col].min()) if not pd.isna(df[col].min()) else 0
            col_info["max"] = float(df[col].max()) if not pd.isna(df[col].max()) else 0
        columns.append(col_info)
        
    dataset_info = {
        "id": dataset_id,
        "name": filename,
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "latest_version": {
            "row_count": row_count,
            "file_size_bytes": len(file_content)
        },
        "filepath": filepath,
        "columns": columns
    }
    
    catalog_entry = {
        "id": dataset_id,
        "name": filename,
        "domain": "Sales" if "sales" in filename.lower() or "revenue" in filename.lower() else "General",
        "description": f"Auto-generated catalog entry for {filename}. Contains {row_count} rows and {col_count} columns.",
        "owner": "DataMind OS",
        "tags": ["auto-inferred", "raw-data"]
    }
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO datasets (id, name, status, created_at, latest_version, filepath, columns)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        dataset_id, filename, dataset_info["status"], dataset_info["created_at"],
        json.dumps(dataset_info["latest_version"]), filepath, json.dumps(columns)
    ))
    
    cursor.execute('''
        INSERT INTO catalog (id, name, domain, description, owner, tags)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        dataset_id, catalog_entry["name"], catalog_entry["domain"],
        catalog_entry["description"], catalog_entry["owner"], json.dumps(catalog_entry["tags"])
    ))
    
    cursor.execute('''
        INSERT OR REPLACE INTO active_dataset (id, dataset_id) VALUES (1, ?)
    ''', (dataset_id,))
    
    conn.commit()
    conn.close()
    
    return dataset_info

def get_active_dataset():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT dataset_id FROM active_dataset WHERE id = 1
    ''')
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
        
    dataset_id = row[0]
    cursor.execute('''
        SELECT id, name, status, created_at, latest_version, filepath, columns
        FROM datasets WHERE id = ?
    ''', (dataset_id,))
    dataset_row = cursor.fetchone()
    conn.close()
    
    if not dataset_row:
        return None
        
    return {
        "id": dataset_row[0],
        "name": dataset_row[1],
        "status": dataset_row[2],
        "created_at": dataset_row[3],
        "latest_version": json.loads(dataset_row[4]),
        "filepath": dataset_row[5],
        "columns": json.loads(dataset_row[6])
    }

def get_dataframe(dataset_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT filepath FROM datasets WHERE id = ?', (dataset_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    filepath = row[0]
    if not os.path.exists(filepath):
        return None
        
    if filepath.endswith(".csv"):
        return pd.read_csv(filepath)
    elif filepath.endswith(".xlsx"):
        return pd.read_excel(filepath)
    return pd.read_csv(filepath)
