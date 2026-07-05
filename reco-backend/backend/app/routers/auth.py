from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
import bcrypt
import hashlib
from datetime import datetime, timedelta
import asyncpg
import time
import os
from dependencies import get_db, get_es

router = APIRouter()

# JWT settings
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class UserRegister(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    email: str
    name: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

def normalize_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_password_hash(password: str) -> str:
    normalized = normalize_password(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(normalized.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    normalized = normalize_password(plain_password)
    return bcrypt.checkpw(
        normalized.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db),
    es = Depends(get_es)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    async with db.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, email, name, created_at FROM users WHERE id = $1",
            user_id
        )
        if user is None:
            raise credentials_exception
        return {
            "id": str(user["id"]),
            "email": user["email"],
            "name": user["name"],
            "created_at": user["created_at"]
        }

async def get_current_user_optional(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)),
    db = Depends(get_db)
):
    """Optional authentication - returns None if not authenticated"""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    async with db.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, email, name, created_at FROM users WHERE id = $1",
            user_id
        )
        if user is None:
            return None
        return {
            "id": str(user["id"]),
            "email": user["email"],
            "name": user["name"],
            "created_at": user["created_at"]
        }

@router.post("/auth/register", response_model=Token)
async def register(
    user_data: UserRegister,
    db = Depends(get_db),
    es = Depends(get_es)
):
    """Đăng ký tài khoản mới"""
    t0 = time.time()
    
    async with db.acquire() as conn:
        # Kiểm tra email đã tồn tại
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            user_data.email
        )
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Tạo user mới
        try:
            # Hash mật khẩu
            password_hash = get_password_hash(user_data.password)

            # Insert user mới
            user_id = await conn.fetchval(
                """
                INSERT INTO users (email, name, password_hash)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                user_data.email, user_data.name, password_hash
            )

        except Exception as e:
            # Bắt mọi lỗi phát sinh (DB, hash, constraint...)
            raise HTTPException(
                status_code=400,   # hoặc 500 nếu muốn báo lỗi server
                detail=f"Could not create user: {str(e)}"
            )

    
    # Tạo token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_id), "email": user_data.email},
        expires_delta=access_token_expires
    )
    
    latency = int((time.time() - t0) * 1000)
    
    # Log event
    try:
        await es.post("/analytics/_doc", json={
            "timestamp": int(time.time() * 1000),
            "event_type": "user_register",
            "user_id": str(user_id),
            "email": user_data.email,
            "latency_ms": latency
        })
    except:
        pass
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user_id),
        "email": user_data.email,
        "name": user_data.name
    }

@router.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db = Depends(get_db),
    es = Depends(get_es)
):
    """Đăng nhập (sử dụng email làm username)"""
    t0 = time.time()
    
    async with db.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, email, name, password_hash FROM users WHERE email = $1",
            form_data.username  # OAuth2PasswordRequestForm sử dụng username field cho email
        )
        
        if not user or not verify_password(form_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Tạo token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["id"]), "email": user["email"]},
        expires_delta=access_token_expires
    )
    
    latency = int((time.time() - t0) * 1000)
    
    # Log event
    try:
        await es.post("/analytics/_doc", json={
            "timestamp": int(time.time() * 1000),
            "event_type": "user_login",
            "user_id": str(user["id"]),
            "email": user["email"],
            "latency_ms": latency
        })
    except:
        pass
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user["id"]),
        "email": user["email"],
        "name": user["name"]
    }

@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Lấy thông tin user hiện tại"""
    return current_user

# Endpoint dùng cho môi trường test – xóa tài khoản được tạo động
class UserDelete(BaseModel):
    email: EmailStr
    password: str

@router.delete("/auth/delete")
async def delete_account(
    user_data: UserDelete,
    db = Depends(get_db)
):
    """Xóa tài khoản (dùng cho test cleanup). Yêu cầu xác thực lại bằng password."""
    async with db.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, password_hash FROM users WHERE email = $1",
            user_data.email
        )
        if not user or not verify_password(user_data.password, user["password_hash"]):
            raise HTTPException(status_code=404, detail="User not found or wrong password")

        await conn.execute(
            "DELETE FROM users WHERE id = $1",
            user["id"]
        )

    return {"detail": "Account deleted"}