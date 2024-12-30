# ChatESG_FastAPI

# 使用 FastAPI 實現後端 API
# 密碼傳輸應該使用 HTTPS
# 真實的 API 調用
# 密碼加密

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import jwt
from datetime import datetime, timedelta
import bcrypt
import uvicorn

# 創建 FastAPI 應用
app = FastAPI()

# 設置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue 開發服務器的地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 新增 salt 輪數設置
BCRYPT_ROUNDS = 12

# JWT 設置
SECRET_KEY = "your-secret-key"  # 在生產環境中應該使用環境變量
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 模擬數據庫
# 修改初始用戶密碼加密方式
fake_users_db = {
    "admin": {
        "username": "admin",
        "password": bcrypt.hashpw("1".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "user_id": "1",
        "avatarUrl": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSYgxhfgMx7eTgoyIVGOHtM_m4KukKe1NdeKQKcFM1ayUvCc5Zpf16w1k2PMn9tcdIjm0A&usqp=CAU",
        "organization": "國立臺中科技大學"
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    password: str


class UserInDB(User):
    user_id: str


def verify_password(plain_password, hashed_password):
    # 修改密碼驗證方法
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password):
    # 修改密碼加密方法
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/api/login")
async def login(form_data: User):
    print(f"Attempting login for user: {form_data.username}")
    user = fake_users_db.get(form_data.username)
    if not user:
        print(f"User not found: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤"
        )
    
    print(f"Verifying password for user: {form_data.username}")
    if not verify_password(form_data.password, user["password"]):
        print(f"Password verification failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤"
        )
    
    # 創建訪問令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, 
        expires_delta=access_token_expires
    )
    
    return {
        "status": "success",
        "access_token": access_token,
        "token_type": "bearer",
        "userID": user["user_id"],
        "username": user["username"]
    }


@app.post("/api/register")
async def register(user: User):
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用戶名已存在"
        )
    
    hashed_password = get_password_hash(user.password)
    user_id = f"user_{len(fake_users_db) + 1}"
    
    fake_users_db[user.username] = {
        "username": user.username,
        "password": hashed_password,
        "user_id": user_id
    }
    
    return {"status": "success", "message": "註冊成功"}


@app.post("/api/user/profile")
async def get_user_profile(user_data: dict):
    user_id = user_data.get("user_id")
    # 使用用户名而不是 user_id 来查找用户
    for username, user in fake_users_db.items():
        if user["user_id"] == user_id:
            return {
                "userName": user["username"],
                "userID": user["user_id"],
                "avatarUrl": user.get("avatarUrl", ""),
                "organization": user.get("organization", "")
            }
    raise HTTPException(status_code=404, detail="未找到用户")


if __name__ == "__main__":
    uvicorn.run("chatESG_FastAPI:app", host="0.0.0.0", port=8000, reload=True)