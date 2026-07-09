# Removed sqlalchemy imports to avoid missing dependency on Windows

# Temporary SQLite DB for Module 1
SQLALCHEMY_DATABASE_URL = "sqlite:///./ai_bi_os.db"

# Mocked out DB
class SessionLocal:
    def close(self):
        pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
