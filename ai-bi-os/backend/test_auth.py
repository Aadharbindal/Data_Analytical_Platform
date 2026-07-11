import os
import sys
import requests

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.core.security import create_access_token
import sqlite3
from app.core.config import DB_PATH

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT id FROM users LIMIT 1")
row = cursor.fetchone()
conn.close()

if row:
    user_id = row['id']
    token = create_access_token(user_id)
    print(f"Got token for {user_id}")
    
    cookies = {"access_token": token}
    res = requests.get("http://127.0.0.1:8000/api/v1/analytics/report.pdf", cookies=cookies)
    print("Status code:", res.status_code)
    if res.status_code != 200:
        print("Response:", res.text)
else:
    print("No users found")
