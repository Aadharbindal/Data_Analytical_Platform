from fastapi.testclient import TestClient
from app.main import app
from app.services.data_processing import get_active_dataset
from app.core.security import create_access_token

client = TestClient(app)

# We need a valid user and to set the active dataset.
# The endpoint depends on get_current_user. Let's mock or use a token.
import os

token = create_access_token({"sub": "admin", "id": "admin_user_id"})
headers = {"Authorization": f"Bearer {token}"}

# set active dataset to food_delivery_FINAL_TEST.csv
# Wait, how is active dataset stored? Probably in sqlite.
import sqlite3
from app.core.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('INSERT OR IGNORE INTO users (id, username, role) VALUES (?, ?, ?)', ('admin_user_id', 'admin', 'admin'))
cursor.execute('INSERT OR IGNORE INTO datasets (id, user_id, filename, file_path, status) VALUES (?, ?, ?, ?, ?)', ('test_dataset', 'admin_user_id', 'food_delivery_FINAL_TEST.csv', 'data/6c7d6c39-4a46-4a54-8841-6bef83a66eca_food_delivery_FINAL_TEST.csv', 'active'))
cursor.execute('UPDATE datasets SET status = "inactive" WHERE user_id = "admin_user_id"')
cursor.execute('UPDATE datasets SET status = "active" WHERE id = "test_dataset"')
conn.commit()

resp = client.post("/api/v1/recommendations/generate", headers=headers)
print("STATUS CODE:", resp.status_code)
print("RESPONSE:", resp.json())
