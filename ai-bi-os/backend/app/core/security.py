import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import SECRET_KEY
from app.core.database import get_db_connection
from app.core.config import DB_PATH

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
PRE_AUTH_TOKEN_EXPIRE_MINUTES = 5

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(subject: str, session_id: Optional[str] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    if session_id:
        to_encode["sid"] = session_id
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: str, session_id: Optional[str] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject)}
    if session_id:
        to_encode["sid"] = session_id
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_pre_auth_token(subject: str) -> str:
    """Short-lived token for the gap between password check and 2FA code check —
    proves the password was already verified without granting real session access."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=PRE_AUTH_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "purpose": "2fa"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_pre_auth_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired verification token")
    if payload.get("purpose") != "2fa" or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid verification token")
    return payload["sub"]

def get_current_user(request: Request, auth_header: HTTPAuthorizationCredentials = Security(security)):
    token = request.cookies.get("access_token")
    if not token and auth_header:
        token = auth_header.credentials
    if not token:
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        session_id = payload.get("sid")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Tokens issued before session tracking existed have no `sid` — treat them
    # as legacy/trusted rather than rejecting already-logged-in users mid-flight.
    if session_id:
        cursor.execute("SELECT revoked FROM sessions WHERE id=%s AND user_id=%s", (session_id, user_id))
        srow = cursor.fetchone()
        if not srow or srow[0]:
            conn.close()
            raise HTTPException(status_code=401, detail="Session revoked")

    cursor.execute("SELECT id, email, full_name, is_active, created_at, totp_enabled FROM users WHERE id=%s", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="User not found")

    if not row[3]: # is_active
        raise HTTPException(status_code=401, detail="Inactive user")

    return {
        "id": row[0],
        "email": row[1],
        "full_name": row[2],
        "created_at": row[4],
        "totp_enabled": bool(row[5]),
        "session_id": session_id
    }
