from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import psycopg2.extras
import sqlite3
import os

# Default to SQLite if DATABASE_URL is not provided
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_bi_os.db")

# Only use check_same_thread for SQLite
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DBAPICursorProxy:
    def __init__(self, cursor, is_postgres):
        self.cursor = cursor
        self.is_postgres = is_postgres
        
    def execute(self, query, params=None):
        if self.is_postgres:
            query = query.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
            query = query.replace('JSON', 'JSONB')
            query = query.replace('?', '%s')
            
        if params is not None:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        return self
        
    def fetchone(self):
        return self.cursor.fetchone()
        
    def fetchall(self):
        return self.cursor.fetchall()
        
    def close(self):
        self.cursor.close()
        
    @property
    def rowcount(self):
        return self.cursor.rowcount

class DBAPIConnectionProxy:
    def __init__(self):
        self.engine = engine
        self.conn = engine.raw_connection()
        self.is_postgres = engine.name == 'postgresql'
        self._row_factory = None
        
    def cursor(self, *args, **kwargs):
        if self.is_postgres:
            kwargs['cursor_factory'] = psycopg2.extras.DictCursor
        cursor = self.conn.cursor(*args, **kwargs)
        return DBAPICursorProxy(cursor, self.is_postgres)
        
    def commit(self):
        self.conn.commit()
        
    def rollback(self):
        self.conn.rollback()
        
    def close(self):
        self.conn.close()

    @property
    def row_factory(self):
        return self._row_factory
        
    @row_factory.setter
    def row_factory(self, value):
        self._row_factory = value
        if not self.is_postgres and value is not None and value != 'None':
            self.conn.row_factory = sqlite3.Row

def get_db_connection():
    return DBAPIConnectionProxy()
