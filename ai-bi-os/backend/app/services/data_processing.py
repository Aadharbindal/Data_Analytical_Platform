import os
import pandas as pd
import uuid
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# In-memory database for mock backend
db = {
    "datasets": {},
    "catalog": [],
    "active_dataset_id": None
}

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
    
    db["datasets"][dataset_id] = dataset_info
    db["active_dataset_id"] = dataset_id
    
    # Auto-generate catalog entry
    catalog_entry = {
        "id": dataset_id,
        "name": filename,
        "domain": "Sales" if "sales" in filename.lower() or "revenue" in filename.lower() else "General",
        "description": f"Auto-generated catalog entry for {filename}. Contains {row_count} rows and {col_count} columns.",
        "owner": "DataMind OS",
        "tags": ["auto-inferred", "raw-data"]
    }
    db["catalog"].append(catalog_entry)
    
    return dataset_info

def get_active_dataset():
    if not db["active_dataset_id"]:
        return None
    return db["datasets"][db["active_dataset_id"]]

def get_dataframe(dataset_id: str):
    dataset_info = db["datasets"].get(dataset_id)
    if not dataset_info:
        return None
    filepath = dataset_info["filepath"]
    if filepath.endswith(".csv"):
        return pd.read_csv(filepath)
    elif filepath.endswith(".xlsx"):
        return pd.read_excel(filepath)
    return pd.read_csv(filepath)
