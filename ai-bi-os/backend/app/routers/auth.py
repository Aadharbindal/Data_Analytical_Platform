import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr
from app.core.database import get_db_connection
import uuid
from datetime import datetime

from app.core.config import DB_PATH
from app.core.security import (
    hash_password, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup")
def signup(user: UserSignup, response: Response):
    import re
    if len(user.password) < 8 or not re.search(r"[A-Za-z]", user.password) or not re.search(r"[0-9]", user.password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters and include a letter and a number.")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    email_lower = user.email.lower()
    cursor.execute("SELECT id FROM users WHERE email=%s", (email_lower,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
        
    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(user.password)
    now = datetime.utcnow().isoformat()
    
    cursor.execute(
        "INSERT INTO users (id, email, password_hash, full_name, created_at, is_active) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, email_lower, hashed_pw, user.full_name, now, 1)
    )
    conn.commit()
    conn.close()
    
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    
    secure_cookies = os.getenv("SECURE_COOKIES", "false").lower() == "true"
    samesite_mode = "none" if secure_cookies else "lax"
    
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True, 
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite=samesite_mode,
        secure=secure_cookies
    )
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token, 
        httponly=True, 
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite=samesite_mode,
        secure=secure_cookies
    )
    
    return {"message": "User created successfully", "access_token": access_token, "token_type": "bearer"}

@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, user: UserLogin, response: Response):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    email_lower = user.email.lower()
    cursor.execute("SELECT id, password_hash, is_active FROM users WHERE email=%s", (email_lower,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not verify_password(user.password, row[1]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    if not row[2]:
        raise HTTPException(status_code=401, detail="Account is inactive")
        
    user_id = row[0]
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    
    secure_cookies = os.getenv("SECURE_COOKIES", "false").lower() == "true"
    samesite_mode = "none" if secure_cookies else "lax"

    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True, 
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite=samesite_mode,
        secure=secure_cookies
    )
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token, 
        httponly=True, 
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite=samesite_mode,
        secure=secure_cookies
    )
    
    return {"message": "Login successful", "access_token": access_token, "token_type": "bearer"}

@router.post("/refresh")
def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
        
    import jwt
    from app.core.config import SECRET_KEY
    from app.core.security import ALGORITHM
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_active FROM users WHERE id=%s", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row or not row[0]:
            raise HTTPException(status_code=401, detail="User inactive or not found")
            
        access_token = create_access_token(user_id)
        secure_cookies = os.getenv("SECURE_COOKIES", "false").lower() == "true"
        samesite_mode = "none" if secure_cookies else "lax"

        response.set_cookie(
            key="access_token", 
            value=access_token, 
            httponly=True, 
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite=samesite_mode,
            secure=secure_cookies
        )
        return {"message": "Token refreshed"}
        
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}

@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return current_user
