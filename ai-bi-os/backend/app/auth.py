from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

security = HTTPBearer()
SECRET_KEY = "enterprise_super_secret_key"
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Simple in-memory rate limiting map for demonstration
rate_limit_store = {}

def rate_limiter(req: Request):
    client_ip = req.client.host if req.client else "127.0.0.1"
    now = datetime.now()
    
    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []
        
    # Remove timestamps older than 1 minute
    rate_limit_store[client_ip] = [t for t in rate_limit_store[client_ip] if now - t < timedelta(minutes=1)]
    
    if len(rate_limit_store[client_ip]) >= 100: # 100 requests per minute
        raise HTTPException(status_code=429, detail="Too Many Requests")
        
    rate_limit_store[client_ip].append(now)
