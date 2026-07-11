import sqlite3
import json

conn = sqlite3.connect("backend/data/datamind.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all insights
cursor.execute("SELECT id, title, audit_sql, confidence, verified, created_at, user_id, dataset_id FROM insights")
rows = [dict(r) for r in cursor.fetchall()]
print("Total insights in DB:", len(rows))

# For first user/dataset
if rows:
    uid = rows[0]['user_id']
    did = rows[0]['dataset_id']
    print(f"Checking for user {uid}, dataset {did}")
    
    cursor.execute('SELECT verified, count(*) as count FROM insights WHERE user_id = ? AND dataset_id = ? GROUP BY verified', (uid, did))
    stats = [dict(r) for r in cursor.fetchall()]
    print("Stats:", stats)
    
    cursor.execute('SELECT id, title, created_at FROM insights WHERE user_id = ? AND dataset_id = ? ORDER BY created_at DESC LIMIT 10', (uid, did))
    audit = [dict(r) for r in cursor.fetchall()]
    print("Audit trail len:", len(audit))
    for a in audit:
        print(a)
        
conn.close()
