import os
from pathlib import Path

# Base Directory of the backend project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Configurable DATA_DIR (default: backend/data)
DATA_DIR_ENV = os.getenv("DATA_DIR")
if DATA_DIR_ENV:
    DATA_DIR = Path(DATA_DIR_ENV).resolve()
else:
    DATA_DIR = BASE_DIR / "data"

os.makedirs(DATA_DIR, exist_ok=True)

# Configurable DB_PATH
DB_PATH_ENV = os.getenv("SQLITE_PATH")
if DB_PATH_ENV:
    DB_PATH = Path(DB_PATH_ENV).resolve()
else:
    DB_PATH = DATA_DIR / "datamind.db"

# CORS Origin
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:3000")

# Max Upload Size in MB
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))

# Backend Port
PORT = int(os.getenv("PORT", "8000"))
