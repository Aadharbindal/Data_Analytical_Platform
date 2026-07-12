import asyncio
import os
import sqlite3
import pandas as pd
from app.routers.recommendations import generate_recommendations
from app.services.data_processing import get_active_dataset, get_dataframe

async def test():
    conn = sqlite3.connect("data/datamind.db")
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT id, user_id, filepath FROM datasets WHERE filepath LIKE '%food_delivery_FINAL_TEST.csv%' LIMIT 1").fetchone()
    if not row:
        print("electronics_sales_BIG.csv not found in DB.")
        return
        
    dataset_id = row["id"]
    user_id = row["user_id"]
    print(f"Testing with Dataset: {row['filepath']}, ID: {dataset_id}, User: {user_id}")
    
    # Check if there is an active_dataset entry for this user
    active_row = conn.execute("SELECT user_id FROM active_dataset WHERE user_id = ?", (user_id,)).fetchone()
    if not active_row:
        conn.execute("INSERT INTO active_dataset (user_id, dataset_id) VALUES (?, ?)", (user_id, dataset_id))
    else:
        conn.execute("UPDATE active_dataset SET dataset_id = ? WHERE user_id = ?", (dataset_id, user_id))
        
    conn.execute("DELETE FROM recommendations WHERE dataset_id = ?", (dataset_id,))
    conn.commit()
    conn.close()
    
    user_mock = {"id": user_id, "username": "test_user"}
    recs = await generate_recommendations(user_mock)
    print(f"Generated {len(recs)} recommendations.")

if __name__ == "__main__":
    asyncio.run(test())
