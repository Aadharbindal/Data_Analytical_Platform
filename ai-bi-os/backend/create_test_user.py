import sqlite3
import uuid
from datetime import datetime
import os
import sys

# Add backend directory to path so we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.security import hash_password
    from app.core.config import DB_PATH
except ImportError as e:
    print(f"Error importing app modules: {e}")
    sys.exit(1)

def create_user(email: str, password: str, full_name: str):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE email=?", (email,))
    if cursor.fetchone():
        print(f"User {email} already exists.")
        conn.close()
        return

    # Create users table if not exists (just in case)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_active INTEGER NOT NULL
        )
    """)

    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(password)
    now = datetime.utcnow().isoformat()
    
    cursor.execute(
        "INSERT INTO users (id, email, password_hash, full_name, created_at, is_active) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, email, hashed_pw, full_name, now, 1)
    )
    conn.commit()
    conn.close()
    print(f"Successfully created user {email}")

if __name__ == "__main__":
    create_user("test@example.com", "Password123", "Test User")
