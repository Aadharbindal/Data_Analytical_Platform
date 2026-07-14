import sqlite3

conn = sqlite3.connect('c:/Users/user/Documents/Data_Analytics/ai-bi-os/backend/data/datamind.db')
print(conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='insights'").fetchall())
print("DATA:", conn.execute("SELECT created_at FROM insights LIMIT 5").fetchall())
