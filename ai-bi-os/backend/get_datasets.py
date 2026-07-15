import sqlite3
conn = sqlite3.connect('data/datamind.db')
datasets = conn.execute("SELECT id, name FROM datasets").fetchall()
print(datasets)
