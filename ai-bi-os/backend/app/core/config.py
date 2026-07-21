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

# Deprecated SQLite Path (kept for import compatibility)
DB_PATH = None



# CORS Origin
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:3000")

# Max Upload Size in MB
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))

# Backend Port
PORT = int(os.getenv("PORT", "8000"))

# Secret Key for Auth
import secrets
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(32)
    print("WARNING: No SECRET_KEY found in environment. Generated a temporary random key for development.")

# AI Model Configuration
# Small/fast model: used for narrow, templated tasks (insight narratives,
# recommendation wording, executive summaries) where the model fills in
# placeholders or lightly rephrases deterministic facts rather than reasoning.
LLM_MODEL = os.getenv("LLM_MODEL", "groq/llama-3.1-8b-instant")
# Larger/more capable model: used for multi-step agentic reasoning (tool
# selection, SQL generation, synthesizing a final answer across several tool
# calls) where quality matters more than the extra latency/cost.
LLM_MODEL_COMPLEX = os.getenv("LLM_MODEL_COMPLEX", "groq/llama-3.3-70b-versatile")

# AWS S3 / Cloud Storage Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")  # Optional, mainly for Supabase/R2
