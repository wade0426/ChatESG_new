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
import aiomysql
import uuid

# 創建 FastAPI 應用
app = FastAPI()

# 設置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 資料庫配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',  # 請根據實際情況修改
    'password': '',  # 請根據實際情況修改
    'db': 'chatesg_new',
    'charset': 'utf8mb4'
}

# 新增 salt 輪數設置
BCRYPT_ROUNDS = 12

# JWT 設置
SECRET_KEY = "your-secret-key"  # 在生產環境中應該使用環境變量
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 默認圖片設置
DEFAULT_USER_AVATAR = "https://raw.githubusercontent.com/wade0426/ChatESG_new/refs/heads/main/userPhoto/user-icons.png"
DEFAULT_ORGANIZATION_LOGO = "https://raw.githubusercontent.com/wade0426/ChatESG_new/refs/heads/main/userPhoto/organization.png"

# 資料庫連接池
async def get_db_pool():
    pool = await aiomysql.create_pool(**DB_CONFIG)
    return pool

# 全域變數儲存連接池
db_pool = None

@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await get_db_pool()

@app.on_event("shutdown")
async def shutdown():
    global db_pool
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    password: str
    userEmail: str

class LoginUser(BaseModel):
    username: str
    password: str

class UserInDB(User):
    user_id: str

class Organization(BaseModel):
    organizationName: str
    organizationDescription: Optional[str] = None
    avatarUrl: Optional[str] = None

class OrganizationResponse(BaseModel):
    status: str
    message: str
    organization_id: Optional[str] = None


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password):
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
async def login(form_data: LoginUser):
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT UserID, UserName, UserPassword, AvatarUrl, OrganizationID FROM Users WHERE UserName = %s",
                (form_data.username,)
            )
            user = await cur.fetchone()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="帳號或密碼錯誤"
                )
            
            if not verify_password(form_data.password, user[2]):  # user[2] 是 UserPassword
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="帳號或密碼錯誤"
                )
            
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user[1]},  # user[1] 是 UserName
                expires_delta=access_token_expires
            )
            
            return {
                "status": "success",
                "access_token": access_token,
                "token_type": "bearer",
                "userID": user[0],  # UserID
                "username": user[1]  # UserName
            }


@app.post("/api/register")
async def register(user: User):
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 檢查使用者名是否已存在
            await cur.execute("SELECT UserName FROM Users WHERE UserName = %s", (user.username,))
            if await cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用戶名已存在"
                )
            
            # 檢查郵箱是否已存在
            await cur.execute("SELECT UserEmail FROM Users WHERE UserEmail = %s", (user.userEmail,))
            if await cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="郵箱已被使用"
                )
            
            # 創建新用戶
            user_id = str(uuid.uuid4())
            hashed_password = get_password_hash(user.password)
            
            await cur.execute("""
                INSERT INTO Users (UserID, UserName, UserPassword, UserEmail, AvatarUrl)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, user.username, hashed_password, user.userEmail, DEFAULT_USER_AVATAR))
            
            await conn.commit()
            
            return {"status": "success", "message": "註冊成功"}


@app.post("/api/user/profile")
async def get_user_profile(user_data: dict):
    user_id = user_data.get("user_id")
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT UserID, UserName, AvatarUrl, OrganizationID
                FROM Users WHERE UserID = %s
            """, (user_id,))
            
            user = await cur.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="未找到使用者")
            
            # 獲取組織名稱
            organization_name = "尚未加入組織"
            if user[3]:  # 如果有組織ID
                await cur.execute("""
                    SELECT OrganizationName 
                    FROM Organizations 
                    WHERE OrganizationID = %s
                """, (user[3],))
                org = await cur.fetchone()
                if org:
                    organization_name = org[0]
            
            return {
                "userName": user[1],
                "userID": user[0],
                "avatarUrl": user[2] or "",
                "organizationID": user[3] or "",
                "organizationName": organization_name
            }


@app.post("/api/user/profile/Personal_Information")
async def get_user_profile_Personal_Information(user_data: dict):
    user_id = user_data.get("user_id")
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 獲取用戶基本信息
            await cur.execute("""
                SELECT u.UserID, u.UserName, u.AvatarUrl, u.OrganizationID, u.UserEmail,
                       o.OrganizationName
                FROM Users u
                LEFT JOIN Organizations o ON u.OrganizationID = o.OrganizationID
                WHERE u.UserID = %s
            """, (user_id,))
            user = await cur.fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail="未找到使用者")
            
            return {
                "status": "success",
                "data": {
                    "userID": user[0],
                    "userName": user[1],
                    "avatarUrl": user[2] or DEFAULT_USER_AVATAR,
                    "organizationID": user[3] or "",
                    "organizationName": user[5] or "尚未加入組織",
                    "email": user[4]
                }
            }


@app.post("/api/organizations", response_model=OrganizationResponse)
async def create_organization(organization: Organization):
    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 檢查組織名稱是否已存在
                await cur.execute(
                    "SELECT OrganizationID FROM Organizations WHERE OrganizationName = %s",
                    (organization.organizationName,)
                )
                if await cur.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="組織名稱已存在"
                    )
                
                # 生成組織ID
                organization_id = str(uuid.uuid4())
                # 生成組織加入代碼（8位大小寫字母和數字）
                organization_code = str(uuid.uuid4())[:8].upper()
                
                # 插入新組織
                await cur.execute("""
                    INSERT INTO Organizations (
                        OrganizationID,
                        OrganizationName,
                        OrganizationDescription,
                        AvatarUrl,
                        OrganizationCode
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    organization_id,
                    organization.organizationName,
                    organization.organizationDescription,
                    organization.avatarUrl or DEFAULT_ORGANIZATION_LOGO,
                    organization_code
                ))
                
                await conn.commit()
                
                return {
                    "status": "success",
                    "message": "組織創建成功",
                    "organization_id": organization_id
                }
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/user/profile/Change_Password")
async def change_password(user_data: dict):
    user_id = user_data.get("user_id")
    current_password = user_data.get("current_password")
    new_password = user_data.get("new_password")
    
    if not all([user_id, current_password, new_password]):
        raise HTTPException(status_code=400, detail="缺少必要參數")
    
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 驗證當前密碼
            await cur.execute("SELECT UserPassword FROM Users WHERE UserID = %s", (user_id,))
            user = await cur.fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail="未找到使用者")
            
            stored_password = user[0]
            if not verify_password(current_password, stored_password):
                raise HTTPException(status_code=400, detail="當前密碼錯誤")
            
            # 更新新密碼
            hashed_new_password = get_password_hash(new_password)
            await cur.execute(
                "UPDATE Users SET UserPassword = %s WHERE UserID = %s",
                (hashed_new_password, user_id)
            )
            await conn.commit()
            
            return {"status": "success", "message": "密碼修改成功"}


@app.post("/api/user/profile/Change_Username")
async def change_username(user_data: dict):
    user_id = user_data.get("user_id")
    new_username = user_data.get("new_username")
    
    if not all([user_id, new_username]):
        raise HTTPException(status_code=400, detail="缺少必要參數")
    
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 檢查新用戶名是否已存在
            await cur.execute("SELECT UserID FROM Users WHERE UserName = %s AND UserID != %s", (new_username, user_id))
            if await cur.fetchone():
                raise HTTPException(status_code=400, detail="用戶名已存在")
            
            # 更新用戶名
            await cur.execute(
                "UPDATE Users SET UserName = %s WHERE UserID = %s",
                (new_username, user_id)
            )
            await conn.commit()
            
            return {"status": "success", "message": "用戶名修改成功"}


if __name__ == "__main__":
    uvicorn.run("chatESG_FastAPI:app", host="0.0.0.0", port=8000, reload=True)