from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# pool_pre_ping issues a cheap liveness check when a connection is checked out
# of the pool, transparently discarding and replacing one the server has since
# closed. Without it, a managed Postgres dropping idle connections (as hosted
# providers routinely do overnight, on restart, or on network blips) leaves
# dead sockets in the pool and every subsequent request fails with
# "server closed the connection unexpectedly" until the app is restarted.
# pool_recycle proactively retires connections before they reach the typical
# server-side idle timeout, so the pre-ping path is rarely even needed.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=280,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PostgresConnectionProxy:
    """A simple wrapper over raw DBAPI connection to provide a DictCursor by default."""
    def __init__(self, engine):
        self.conn = engine.raw_connection()
        
    def cursor(self, *args, **kwargs):
        kwargs['cursor_factory'] = psycopg2.extras.DictCursor
        return self.conn.cursor(*args, **kwargs)
        
    def commit(self):
        self.conn.commit()
        
    def rollback(self):
        self.conn.rollback()
        
    def close(self):
        self.conn.close()

def get_db_connection():
    return PostgresConnectionProxy(engine)
