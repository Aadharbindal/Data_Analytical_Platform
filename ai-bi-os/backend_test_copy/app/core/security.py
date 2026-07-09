from typing import Optional
from datetime import datetime, timedelta
# In a real app, use PyJWT or similar for token generation
# from jose import jwt

SECRET_KEY = "super-secret-key-for-development"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    # return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return f"mock_token_{to_encode}"

def verify_token(token: str):
    # return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return {"sub": "user_id", "role": "admin"}
