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
from datetime import datetime, timedelta, timezone
import bcrypt
import uvicorn
import aiomysql
import uuid
import json
import random
import string
from contextlib import asynccontextmanager
from ai_generate import GeminiGenerator
from dotenv import load_dotenv
import os
# 圖片生成
from mermaid import mermaid_to_image

# 載入 .env 檔案
load_dotenv()

api_keys = list(json.loads(os.getenv("api_keys")))
model_name = os.getenv("model_name")
config = os.getenv("config")
config = dict(json.loads(config))
base_url = os.getenv("base_url")
max_retry = int(os.getenv("max_retry"))


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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時執行
    global db_pool
    db_pool = await get_db_pool()
    yield
    # 關閉時執行
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()

# 創建 FastAPI 應用
app = FastAPI(lifespan=lifespan)

# 設置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    password: str

class LoginUser(BaseModel):
    username: str
    password: str

class UserInDB(User):
    user_id: str

class Organization(BaseModel):
    organizationName: str
    organizationDescription: Optional[str] = None
    avatarUrl: Optional[str] = None
    user_id: str
    purchaseType: str = "Free"  # 默認為免費版
    apiCallQuota: Optional[int] = 10000  # 默認API配額
    maxMembers: Optional[int] = 5  # 默認最大成員數

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
            # 查詢用戶信息，包含帳戶狀態
            await cur.execute(
                """SELECT UserID, UserName, UserPassword, AvatarUrl, OrganizationID, 
                   AccountStatus, LoginAttempts 
                   FROM Users WHERE UserName = %s""",
                (form_data.username,)
            )
            user = await cur.fetchone()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="帳號或密碼錯誤"
                )
            
            # 檢查帳戶狀態
            if user[5] == 'locked':
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="帳戶已被鎖定，請聯繫管理員"
                )
            elif user[5] == 'disabled':
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="帳戶已被禁用"
                )
            
            # 驗證密碼
            if not verify_password(form_data.password, user[2]):
                # 更新登錄嘗試次數
                new_attempts = user[6] + 1
                await cur.execute(
                    "UPDATE Users SET LoginAttempts = %s WHERE UserID = %s",
                    (new_attempts, user[0])
                )
                await conn.commit()
                
                # 如果登錄嘗試次數過多，鎖定帳戶
                if new_attempts >= 5:  # 可以根據需求調整次數
                    await cur.execute(
                        "UPDATE Users SET AccountStatus = 'locked' WHERE UserID = %s",
                        (user[0],)
                    )
                    await conn.commit()
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="登錄嘗試次數過多，帳戶已被鎖定"
                    )
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="帳號或密碼錯誤"
                )
            
            # 登錄成功，重置登錄嘗試次數並更新最後登錄時間
            current_time = datetime.now(timezone.utc)
            await cur.execute(
                """UPDATE Users 
                   SET LoginAttempts = 0, 
                       LastLoginAt = %s,
                       UpdatedAt = %s
                   WHERE UserID = %s""",
                (current_time, current_time, user[0])
            )
            await conn.commit()
            
            # 生成訪問令牌
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user[1]},  # user[1] 是 UserName
                expires_delta=access_token_expires
            )
            
            # 將 BINARY(16) 格式的 UUID 轉換為字符串
            user_id_str = uuid.UUID(bytes=user[0]).hex if user[0] else None
            organization_id_str = uuid.UUID(bytes=user[4]).hex if user[4] else None
            
            return {
                "status": "success",
                "access_token": access_token,
                "token_type": "bearer",
                "userID": user_id_str,
                "username": user[1],
                "organizationID": organization_id_str
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
            user_id = uuid.uuid4().bytes  # 轉換為BINARY(16)格式
            hashed_password = get_password_hash(user.password)
            current_time = datetime.now(timezone.utc)  # 使用timezone.utc
            
            await cur.execute("""
                INSERT INTO Users (
                    UserID, UserName, UserPassword, UserEmail, AvatarUrl,
                    CreatedAt, UpdatedAt, LastLoginAt, LoginAttempts, 
                    AccountStatus, PasswordChangedAt
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, user.username, hashed_password, user.userEmail, DEFAULT_USER_AVATAR,
                current_time, current_time, None, 0, 
                'active', current_time
            ))
            
            await conn.commit()
            
            return {"status": "success", "message": "註冊成功"}


# 獲取使用者個人資料
@app.post("/api/user/profile/Personal_Information")
async def get_user_profile_Personal_Information(user_data: dict):
    try:
        # 將字符串格式的user_id轉換為BINARY(16)格式
        user_id = uuid.UUID(user_data.get("user_id")).bytes
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="無效的用戶ID格式")

    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 獲取用戶基本信息，加入 OrganizationMembers 表的關聯
            await cur.execute("""
                SELECT u.UserID, u.UserName, u.AvatarUrl, u.OrganizationID, u.UserEmail,
                       o.OrganizationName, u.AccountStatus, u.LastLoginAt, u.OrganizationID
                FROM Users u
                LEFT JOIN OrganizationMembers om ON u.UserID = om.UserID
                LEFT JOIN Organizations o ON om.OrganizationID = o.OrganizationID
                WHERE u.UserID = %s
            """, (user_id,))
            user = await cur.fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail="未找到使用者")
            
            # 獲取用戶的所有角色信息
            await cur.execute("""
                SELECT r.RoleID, r.RoleName, r.Color
                FROM UserRoles ur
                JOIN Roles r ON ur.RoleID = r.RoleID
                WHERE ur.UserID = %s
            """, (user_id,))
            roles = await cur.fetchall()
            
            # 將BINARY(16)格式的UUID轉換為字符串
            user_id_str = uuid.UUID(bytes=user[0]).hex if user[0] else None
            organization_id_str = uuid.UUID(bytes=user[3]).hex if user[3] else None
            user_organization_id_str = uuid.UUID(bytes=user[8]).hex if user[8] else None
            
            # 處理角色信息
            user_roles = []
            for role in roles:
                role_id_str = uuid.UUID(bytes=role[0]).hex if role[0] else None
                user_roles.append({
                    "roleID": role_id_str,
                    "roleName": role[1],
                    "roleColor": role[2]
                })
            
            return {
                "status": "success",
                "data": {
                    "userID": user_id_str,
                    "userName": user[1],
                    "avatarUrl": user[2] or DEFAULT_USER_AVATAR,
                    "organizationID": organization_id_str,
                    "organizationName": user[5] or "尚未加入組織",
                    "email": user[4],
                    "accountStatus": user[6],
                    "lastLoginAt": user[7].isoformat() if user[7] else None,
                    "organizationRoles": user_roles,
                    "userOrganizationID": user_organization_id_str
                }
            }


# 建立組織
@app.post("/api/organizations/found", response_model=OrganizationResponse)
async def create_organization(organization: Organization):
    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 檢查組織名稱是否已存在
                await cur.execute(
                    "SELECT OrganizationID FROM Organizations WHERE OrganizationName = %s AND IsDeleted = FALSE",
                    (organization.organizationName,)
                )
                if await cur.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="組織名稱已存在"
                    )
                
                # 生成組織ID (BINARY(16)格式)
                organization_id = uuid.uuid4().bytes
                # 生成組織加入代碼（8位大小寫字母和數字）
                organization_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                
                # 插入新組織
                await cur.execute("""
                    INSERT INTO Organizations (
                        OrganizationID,
                        OrganizationName,
                        OrganizationDescription,
                        AvatarUrl,
                        OrganizationCode,
                        OwnerID,
                        PurchaseType,
                        APICallQuota,
                        MaxMembers,
                        ExpiryDate,
                        IsDeleted
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    organization_id,
                    organization.organizationName,
                    organization.organizationDescription,
                    organization.avatarUrl or DEFAULT_ORGANIZATION_LOGO,
                    organization_code,
                    uuid.UUID(organization.user_id).bytes,  # 轉換為 BINARY(16)
                    organization.purchaseType,
                    organization.apiCallQuota,
                    organization.maxMembers,
                    None,  # ExpiryDate，預設為 None
                    False  # IsDeleted
                ))

                # 將創建者的組織ID設置為組織ID
                await cur.execute(
                    "UPDATE Users SET OrganizationID = %s WHERE UserID = %s",
                    (organization_id, uuid.UUID(organization.user_id).bytes)
                )

                # 創建預設角色
                default_roles = ["一般", "資訊部", "行銷部"]
                for role_name in default_roles:
                    role_id = uuid.uuid4().bytes
                    # 創建角色
                    await cur.execute("""
                        INSERT INTO Roles (RoleID, OrganizationID, RoleName)
                        VALUES (%s, %s, %s)
                    """, (role_id, organization_id, role_name))
                    
                    # 如果是資訊部角色，將其分配給創建者
                    if role_name == "資訊部":
                        await cur.execute("""
                            INSERT INTO UserRoles (UserID, RoleID, OrganizationID)
                            VALUES (%s, %s, %s)
                        """, (uuid.UUID(organization.user_id).bytes, role_id, organization_id))

                # 更新組織成員資料表
                await cur.execute("""
                    INSERT INTO OrganizationMembers 
                    (OrganizationID, UserID, CreatedAt) 
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                """, (organization_id, uuid.UUID(organization.user_id).bytes))
                
                await conn.commit()
                
                return {
                    "status": "success",
                    "message": "組織創建成功",
                    "organization_id": uuid.UUID(bytes=organization_id).hex
                }
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/user/profile/Change_Password")
async def change_password(user_data: dict):
    try:
        # 將字符串格式的user_id轉換為BINARY(16)格式
        user_id = uuid.UUID(user_data.get("user_id")).bytes
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="無效的用戶ID格式")
        
    current_password = user_data.get("current_password")
    new_password = user_data.get("new_password")
    
    if not all([current_password, new_password]):
        raise HTTPException(status_code=400, detail="缺少必要參數")
    
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 驗證當前密碼和檢查帳戶狀態
            await cur.execute(
                "SELECT UserPassword, AccountStatus FROM Users WHERE UserID = %s",
                (user_id,)
            )
            user = await cur.fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail="未找到使用者")
            
            # 檢查帳戶狀態
            if user[1] == 'locked':
                raise HTTPException(status_code=400, detail="帳戶已被鎖定，無法修改密碼")
            elif user[1] == 'disabled':
                raise HTTPException(status_code=400, detail="帳戶已被禁用")
            
            stored_password = user[0]
            if not verify_password(current_password, stored_password):
                raise HTTPException(status_code=400, detail="當前密碼錯誤")
            
            # 更新新密碼和密碼修改時間
            current_time = datetime.now(timezone.utc)
            hashed_new_password = get_password_hash(new_password)
            await cur.execute(
                """UPDATE Users 
                   SET UserPassword = %s,
                       PasswordChangedAt = %s,
                       UpdatedAt = %s
                   WHERE UserID = %s""",
                (hashed_new_password, current_time, current_time, user_id)
            )
            await conn.commit()
            
            return {"status": "success", "message": "密碼修改成功"}


@app.post("/api/user/profile/Change_Username")
async def change_username(user_data: dict):
    try:
        # 將字符串格式的user_id轉換為BINARY(16)格式
        user_id = uuid.UUID(user_data.get("user_id")).bytes
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="無效的用戶ID格式")
        
    new_username = user_data.get("new_username")
    
    if not new_username:
        raise HTTPException(status_code=400, detail="缺少新用戶名")
    
    # 驗證用戶名長度
    if len(new_username) > 100:
        raise HTTPException(status_code=400, detail="用戶名長度不能超過100個字符")
    
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # 檢查用戶是否存在
                await cur.execute("SELECT UserID FROM Users WHERE UserID = %s", (user_id,))
                if not await cur.fetchone():
                    raise HTTPException(status_code=404, detail="用戶不存在")
                
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
                
            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"修改用戶名失敗: {str(e)}")


# 審核後加入組織
@app.post("/api/organizations/check_join")
async def join_organization(join_data: dict):
    try:
        # 獲取必要參數
        application_id = join_data.get("application_id") #流水號
        reviewer_id = join_data.get("reviewer_id") #審核者ID
        is_approved = join_data.get("is_approved", False) #是否通過
        review_message = join_data.get("review_message", "無") #審核回覆訊息
        
        if not all([application_id, reviewer_id]):
            raise HTTPException(status_code=400, detail="缺少必要參數")
            
        # 將字符串格式的reviewer_id轉換為BINARY(16)格式
        reviewer_id_binary = uuid.UUID(reviewer_id).bytes
        
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()
                    
                    # 獲取申請信息
                    await cur.execute("""
                        SELECT a.ApplicantID, a.OrganizationID, a.ApplicationStatus
                        FROM OrganizationApplications a
                        WHERE a.ApplicationID = %s
                    """, (application_id,))
                    
                    application = await cur.fetchone()
                    if not application:
                        raise HTTPException(status_code=404, detail="找不到該申請記錄")
                    
                    if application[2] != 'pending':
                        raise HTTPException(status_code=400, detail="該申請已經被處理過")
                    
                    # 更新申請狀態
                    new_status = 'approved' if is_approved else 'rejected'
                    current_time = datetime.now(timezone.utc)
                    
                    await cur.execute("""
                        UPDATE OrganizationApplications
                        SET ApplicationStatus = %s,
                            ReviewerID = %s,
                            ReviewMessage = %s,
                            ReviewedAt = %s
                        WHERE ApplicationID = %s
                    """, (new_status, reviewer_id_binary, review_message, current_time, application_id))
                    
                    if is_approved:
                        # 檢查用戶是否已經在其他組織中
                        await cur.execute(
                            "SELECT OrganizationID FROM Users WHERE UserID = %s",
                            (application[0],)
                        )
                        user_org = await cur.fetchone()
                        if user_org and user_org[0]:
                            raise HTTPException(status_code=400, detail="該用戶已經是其他組織的成員")
                        
                        # 檢查用戶是否已經在組織成員表中
                        await cur.execute("""
                            SELECT OrganizationMemberID 
                            FROM OrganizationMembers 
                            WHERE OrganizationID = %s AND UserID = %s
                        """, (application[1], application[0]))
                        
                        if not await cur.fetchone():
                            # 將用戶加入組織
                            await cur.execute(
                                "UPDATE Users SET OrganizationID = %s WHERE UserID = %s",
                                (application[1], application[0])
                            )
                            
                            # 添加到組織成員表
                            await cur.execute("""
                                INSERT INTO OrganizationMembers (OrganizationID, UserID)
                                VALUES (%s, %s)
                            """, (application[1], application[0]))
                        
                        # 為新成員添加默認角色（一般）
                        await cur.execute("""
                            SELECT RoleID FROM Roles 
                            WHERE OrganizationID = %s AND RoleName = '一般'
                        """, (application[1],))
                        
                        default_role = await cur.fetchone()
                        if default_role:
                            # 檢查用戶是否已經有這個角色
                            await cur.execute("""
                                SELECT 1 FROM UserRoles 
                                WHERE UserID = %s AND RoleID = %s AND OrganizationID = %s
                            """, (application[0], default_role[0], application[1]))
                            
                            if not await cur.fetchone():
                                await cur.execute("""
                                    INSERT INTO UserRoles (UserID, RoleID, OrganizationID)
                                    VALUES (%s, %s, %s)
                                """, (application[0], default_role[0], application[1]))
                    
                    await conn.commit()
                    return {
                        "status": "success",
                        "message": "申請審核完成",
                        "approved": is_approved
                    }
                    
                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"審核失敗: {str(e)}")
                    
    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的ID格式")


# 申請加入組織
@app.post("/api/organizations/apply")
async def apply_to_organization(data: dict):
    try:
        # 獲取必要參數
        user_id = data.get("user_id")
        organization_code = data.get("organization_code")
        application_message = data.get("application_message", "")

        if not all([user_id, organization_code]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的user_id轉換為BINARY(16)格式
        user_id_binary = uuid.UUID(user_id).bytes

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 檢查用戶是否已經在組織中
                    await cur.execute(
                        "SELECT OrganizationID FROM Users WHERE UserID = %s",
                        (user_id_binary,)
                    )
                    user = await cur.fetchone()
                    if user and user[0]:
                        raise HTTPException(status_code=400, detail="您已經是其他組織的成員")

                    # 查找組織代碼對應的組織
                    await cur.execute(
                        "SELECT OrganizationID FROM Organizations WHERE OrganizationCode = %s AND IsDeleted = FALSE",
                        (organization_code,)
                    )
                    organization = await cur.fetchone()
                    if not organization:
                        raise HTTPException(status_code=404, detail="無效的組織代碼")

                    # 檢查是否已經有待處理的申請
                    await cur.execute("""
                        SELECT ApplicationStatus 
                        FROM OrganizationApplications 
                        WHERE ApplicantID = %s AND OrganizationID = %s 
                        AND ApplicationStatus = 'pending'
                    """, (user_id_binary, organization[0]))

                    if await cur.fetchone():
                        raise HTTPException(status_code=400, detail="您已經有一個待處理的申請")

                    # 檢查是否已經是組織成員
                    await cur.execute(
                        "SELECT OrganizationMemberID FROM OrganizationMembers WHERE OrganizationID = %s AND UserID = %s",
                        (organization[0], user_id_binary)
                    )
                    if await cur.fetchone():
                        raise HTTPException(status_code=400, detail="您已經是該組織的成員")

                    # 創建新的申請記錄
                    await cur.execute("""
                        INSERT INTO OrganizationApplications 
                        (ApplicantID, OrganizationID, ApplicationStatus, ApplicationMessage, CreatedAt)
                        VALUES (%s, %s, 'pending', %s, CURRENT_TIMESTAMP)
                    """, (user_id_binary, organization[0], application_message))

                    # 提交事務
                    await conn.commit()

                    return {
                        "status": "success",
                        "message": "申請已成功提交，請等待組織管理員審核"
                    }

                except Exception as e:
                    # 發生錯誤時回滾事務
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"申請失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的用戶ID格式")


# 取得組織申請列表
@app.post("/api/organizations/get_applications")
async def get_applications(data: dict):
    try:
        # 將字符串格式的organization_id轉換為BINARY(16)格式
        organization_id = uuid.UUID(data.get("organization_id")).bytes
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="無效的組織ID格式")
    
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # 獲取待處理的申請列表
                await cur.execute("""
                    SELECT 
                        oa.ApplicationID,
                        oa.ApplicantID,
                        u.UserName,
                        u.UserEmail,
                        u.AvatarUrl,
                        u.CreatedAt,
                        oa.ApplicationMessage,
                        oa.CreatedAt as ApplicationDate
                    FROM OrganizationApplications oa
                    JOIN Users u ON oa.ApplicantID = u.UserID
                    WHERE oa.OrganizationID = %s 
                    AND oa.ApplicationStatus = 'pending'
                    ORDER BY oa.CreatedAt DESC
                """, (organization_id,))
                
                applications = await cur.fetchall()
                
                # 格式化返回數據
                application_list = []
                for app in applications:
                    application_list.append({
                        "id": app[0],  # ApplicationID
                        "applicantId": uuid.UUID(bytes=app[1]).hex,  # ApplicantID
                        "name": app[2],  # UserName
                        "email": app[3],  # UserEmail
                        "avatarUrl": app[4] or DEFAULT_USER_AVATAR,  # AvatarUrl
                        "userCreatedAt": app[5].isoformat() if app[5] else None,  # User CreatedAt
                        "applicationMessage": app[6],  # ApplicationMessage
                        "applicationDate": app[7].isoformat() if app[7] else None  # Application CreatedAt
                    })
                
                return {
                    "status": "success",
                    "data": application_list
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"獲取申請列表失敗: {str(e)}")


# 獲取組織訊息
@app.post("/api/organizations/info")
async def get_organization_info(data: dict):
    try:
        # 將字符串格式的organization_id轉換為BINARY(16)格式
        organization_id = uuid.UUID(data.get("organization_id")).bytes
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="無效的組織ID格式")
    
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # 開始事務並設置隔離級別為REPEATABLE READ
                await conn.begin()
                await cur.execute("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ")
                
                # 獲取組織基本信息
                await cur.execute("""
                    SELECT 
                        o.OrganizationID,
                        o.OrganizationName,
                        o.OrganizationDescription,
                        o.AvatarUrl,
                        o.OrganizationCode,
                        o.OwnerID,
                        o.PurchaseType,
                        o.APICallQuota,
                        o.MaxMembers,
                        o.CreatedAt,
                        o.UpdatedAt,
                        o.ExpiryDate,
                        u.UserName as OwnerName,
                        (SELECT COUNT(*) FROM OrganizationMembers WHERE OrganizationID = o.OrganizationID) as MemberCount
                    FROM Organizations o
                    LEFT JOIN Users u ON o.OwnerID = u.UserID
                    WHERE o.OrganizationID = %s AND o.IsDeleted = FALSE
                    FOR UPDATE
                """, (organization_id,))
                
                org = await cur.fetchone()
                if not org:
                    await conn.rollback()
                    raise HTTPException(status_code=404, detail="未找到組織")
                
                # 獲取組織成員列表及其角色
                await cur.execute("""
                    SELECT 
                        u.UserID,
                        u.UserName,
                        u.AvatarUrl,
                        u.UserEmail,
                        om.CreatedAt
                    FROM OrganizationMembers om
                    JOIN Users u ON om.UserID = u.UserID
                    WHERE om.OrganizationID = %s
                    ORDER BY om.CreatedAt ASC, u.UserID ASC
                    FOR UPDATE
                """, (organization_id,))
                
                members = await cur.fetchall()
                members_list = []
                
                for member in members:
                    # 使用 FOR UPDATE 鎖定查詢結果
                    await cur.execute("""
                        SELECT DISTINCT r.RoleName, r.Color
                        FROM UserRoles ur
                        JOIN Roles r ON r.RoleID = ur.RoleID
                        WHERE ur.UserID = %s AND ur.OrganizationID = %s
                        ORDER BY r.CreatedAt ASC, r.RoleName ASC, r.RoleID ASC
                        FOR UPDATE
                    """, (member[0], organization_id))
                    
                    roles = await cur.fetchall()
                    roles_info = [{"roleName": role[0], "roleColor": role[1]} for role in roles]
                    
                    members_list.append({
                        "userID": uuid.UUID(bytes=member[0]).hex,
                        "name": member[1],
                        "avatarUrl": member[2] or DEFAULT_USER_AVATAR,
                        "email": member[3],
                        "roles": roles_info,
                        "joinedAt": member[4].isoformat() if member[4] else None
                    })
                
                # 獲取組織的所有可用角色
                await cur.execute("""
                    SELECT RoleName, Color
                    FROM Roles
                    WHERE OrganizationID = %s
                    ORDER BY CreatedAt ASC, RoleName ASC, RoleID ASC
                    FOR UPDATE
                """, (organization_id,))
                
                available_roles = [{"roleName": role[0], "roleColor": role[1]} for role in await cur.fetchall()]
                
                # 提交事務
                await conn.commit()
                
                return {
                    "status": "success",
                    "data": {
                        "id": uuid.UUID(bytes=org[0]).hex,
                        "name": org[1],
                        "description": org[2],
                        "avatarUrl": org[3] or DEFAULT_ORGANIZATION_LOGO,
                        "code": org[4],
                        "owner": {
                            "id": uuid.UUID(bytes=org[5]).hex if org[5] else None,
                            "name": org[12]
                        },
                        "purchaseType": org[6],
                        "apiCallQuota": org[7],
                        "maxMembers": org[8],
                        "expiryDate": org[11].isoformat() if org[11] else None,
                        "roles": available_roles,
                        "memberCount": org[13],
                        "members": members_list,
                        "createdAt": org[9].isoformat() if org[9] else None,
                        "updatedAt": org[10].isoformat() if org[10] else None
                    }
                }
                
            except Exception as e:
                # 如果發生錯誤，回滾事務
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"獲取組織信息失敗: {str(e)}")


# 通過用戶ID獲取組織訊息
@app.post("/api/organizations/get_by_user")
async def get_organization_by_user(data: dict):
    try:
        # 將字符串格式的user_id轉換為BINARY(16)格式
        user_id = uuid.UUID(data.get("user_id")).bytes
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="無效的用戶ID格式")
    
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await conn.begin()
            # 設置事務隔離級別
            await cur.execute("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            try:
                await cur.execute("""
                    SELECT o.OrganizationID, o.OrganizationName, o.OrganizationCode, o.AvatarUrl
                    FROM OrganizationMembers om
                    LEFT JOIN Organizations o ON om.OrganizationID = o.OrganizationID
                    WHERE om.UserID = %s AND o.IsDeleted = FALSE
                """, (user_id,))
                
                result = await cur.fetchone()
                if not result:
                    await conn.commit()
                    return {"status": "success", "data": None}
                
                response = {
                    "status": "success",
                    "data": {
                        "organization_id": uuid.UUID(bytes=result[0]).hex,
                        "organization_name": result[1],
                        "organization_code": result[2],
                        "avatar_url": result[3] or DEFAULT_ORGANIZATION_LOGO
                    }
                }
                await conn.commit()
                return response
                
            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"獲取組織訊息失敗: {str(e)}")


# 更新組織成員角色
@app.post("/api/organizations/update_member_roles")
async def update_member_roles(data: dict):
    user_id = data.get("user_id")
    roles = data.get("roles")
    organization_id = data.get("organization_id")
    
    if not all([user_id, roles, organization_id]):
        raise HTTPException(status_code=400, detail="缺少必要參數")
    
    # 確保 roles 是列表
    if not isinstance(roles, list):
        raise HTTPException(status_code=400, detail="roles 必須是列表")
    
    try:
        # 將字符串格式的 ID 轉換為 BINARY(16)
        user_id_binary = uuid.UUID(user_id).bytes
        organization_id_binary = uuid.UUID(organization_id).bytes
    except ValueError:
        raise HTTPException(status_code=400, detail="無效的 ID 格式")
    
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # 開始事務
                await conn.begin()
                
                # 檢查用戶是否屬於該組織
                await cur.execute("""
                    SELECT OrganizationMemberID 
                    FROM OrganizationMembers 
                    WHERE UserID = %s AND OrganizationID = %s
                """, (user_id_binary, organization_id_binary))
                
                if not await cur.fetchone():
                    raise HTTPException(status_code=404, detail="找不到該組織成員")
                
                # 刪除用戶現有的角色
                await cur.execute("""
                    DELETE FROM UserRoles 
                    WHERE UserID = %s AND OrganizationID = %s
                """, (user_id_binary, organization_id_binary))
                
                # 獲取角色ID並添加新的角色
                for role_name in roles:
                    # 檢查角色是否存在，如果不存在則創建
                    await cur.execute("""
                        SELECT RoleID, Color, Description
                        FROM Roles 
                        WHERE OrganizationID = %s AND RoleName = %s
                    """, (organization_id_binary, role_name))
                    
                    role = await cur.fetchone()
                    if not role:
                        # 如果角色不存在，創建新角色
                        role_id = uuid.uuid4().bytes
                        await cur.execute("""
                            INSERT INTO Roles (RoleID, OrganizationID, RoleName, Color, Description)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (role_id, organization_id_binary, role_name, '#808080', None))
                    else:
                        role_id = role[0]
                    
                    # 添加用戶角色關聯
                    await cur.execute("""
                        INSERT INTO UserRoles (UserID, RoleID, OrganizationID)
                        VALUES (%s, %s, %s)
                    """, (user_id_binary, role_id, organization_id_binary))
                
                await conn.commit()
                return {"status": "success", "message": "成員身份組更新成功"}
                
            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"更新失敗: {str(e)}")


# 更新組織身份組資訊
@app.post("/api/organizations/update_role")
async def update_role(data: dict):
    try:
        # 獲取必要參數
        organization_id = data.get("organization_id")
        original_role_name = data.get("original_role_name")
        new_role_name = data.get("new_role_name")
        new_role_color = data.get("new_role_color")

        if not all([organization_id, original_role_name, new_role_name, new_role_color]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的organization_id轉換為BINARY(16)格式
        organization_id_binary = uuid.UUID(organization_id).bytes

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 檢查原始角色是否存在
                    await cur.execute("""
                        SELECT RoleID 
                        FROM Roles 
                        WHERE OrganizationID = %s AND RoleName = %s
                    """, (organization_id_binary, original_role_name))

                    role = await cur.fetchone()
                    if not role:
                        raise HTTPException(status_code=404, detail="找不到指定的角色")

                    # 如果要更改角色名稱，檢查新角色名稱是否已存在
                    if original_role_name != new_role_name:
                        await cur.execute("""
                            SELECT RoleID 
                            FROM Roles 
                            WHERE OrganizationID = %s AND RoleName = %s
                        """, (organization_id_binary, new_role_name))
                        
                        if await cur.fetchone():
                            raise HTTPException(status_code=400, detail="新角色名稱已存在")

                    # 更新角色資訊
                    await cur.execute("""
                        UPDATE Roles 
                        SET RoleName = %s,
                            Color = %s,
                            Description = NULL
                        WHERE OrganizationID = %s AND RoleName = %s
                    """, (new_role_name, new_role_color, organization_id_binary, original_role_name))

                    await conn.commit()
                    print(f"角色更新成功: {original_role_name} -> {new_role_name}")
                    return {"status": "success", "message": "角色更新成功"}

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"更新失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的組織ID格式")


# 新增身份組
@app.post("/api/organizations/add_role")
async def add_role(data: dict):
    try:
        # 獲取必要參數
        organization_id = data.get("organization_id")
        role_name = data.get("role_name")
        role_description = data.get("role_description")
        role_color = data.get("role_color", "#808080")  # 如果未提供顏色，使用默認灰色

        if not all([organization_id, role_name]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的organization_id轉換為BINARY(16)格式
        organization_id_binary = uuid.UUID(organization_id).bytes

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 檢查組織是否存在
                    await cur.execute("""
                        SELECT OrganizationID 
                        FROM Organizations 
                        WHERE OrganizationID = %s AND IsDeleted = FALSE
                    """, (organization_id_binary,))

                    if not await cur.fetchone():
                        raise HTTPException(status_code=404, detail="找不到指定的組織")

                    # 檢查角色名稱是否已存在於該組織
                    await cur.execute("""
                        SELECT RoleID 
                        FROM Roles 
                        WHERE OrganizationID = %s AND RoleName = %s
                    """, (organization_id_binary, role_name))

                    if await cur.fetchone():
                        raise HTTPException(status_code=400, detail="該角色名稱已存在")

                    # 生成新的角色ID
                    role_id = uuid.uuid4().bytes

                    # 插入新角色
                    await cur.execute("""
                        INSERT INTO Roles (
                            RoleID, 
                            OrganizationID, 
                            RoleName, 
                            Description, 
                            Color
                        ) VALUES (%s, %s, %s, %s, %s)
                    """, (role_id, organization_id_binary, role_name, role_description, role_color))

                    await conn.commit()
                    return {
                        "status": "success",
                        "message": "角色創建成功",
                        "data": {
                            "role_id": uuid.UUID(bytes=role_id).hex,
                            "role_name": role_name,
                            "role_color": role_color
                        }
                    }

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"創建角色失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的組織ID格式")


# 刪除身份組
@app.post("/api/organizations/delete_role")
async def delete_role(data: dict):
    try:
        # 獲取必要參數
        organization_id = data.get("organization_id")
        role_name = data.get("role_name")

        if not all([organization_id, role_name]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的organization_id轉換為BINARY(16)格式
        organization_id_binary = uuid.UUID(organization_id).bytes

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 檢查組織是否存在
                    await cur.execute("""
                        SELECT OrganizationID 
                        FROM Organizations 
                        WHERE OrganizationID = %s AND IsDeleted = FALSE
                    """, (organization_id_binary,))

                    if not await cur.fetchone():
                        raise HTTPException(status_code=404, detail="找不到指定的組織")

                    # 檢查角色是否存在
                    await cur.execute("""
                        SELECT RoleID 
                        FROM Roles 
                        WHERE OrganizationID = %s AND RoleName = %s
                    """, (organization_id_binary, role_name))

                    role = await cur.fetchone()
                    if not role:
                        raise HTTPException(status_code=404, detail="找不到指定的角色")

                    # 檢查是否為預設角色（一般、資訊部、行銷部）
                    if role_name in ["一般", "資訊部", "行銷部"]:
                        raise HTTPException(status_code=400, detail="無法刪除預設角色")

                    # 先刪除用戶與該角色的關聯
                    await cur.execute("""
                        DELETE FROM UserRoles 
                        WHERE RoleID = %s AND OrganizationID = %s
                    """, (role[0], organization_id_binary))

                    # 刪除角色
                    await cur.execute("""
                        DELETE FROM Roles 
                        WHERE RoleID = %s AND OrganizationID = %s
                    """, (role[0], organization_id_binary))

                    await conn.commit()
                    return {"status": "success", "message": "角色刪除成功"}

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"刪除角色失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的組織ID格式")


# 刪除組織成員
@app.post("/api/organizations/delete_member")
async def delete_member(data: dict):
    try:
        # 獲取必要參數
        user_id = data.get("user_id")
        organization_id = data.get("organization_id")

        if not all([user_id, organization_id]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的ID轉換為BINARY(16)格式
        user_id_binary = uuid.UUID(user_id).bytes
        organization_id_binary = uuid.UUID(organization_id).bytes

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 檢查用戶是否存在於組織中
                    await cur.execute("""
                        SELECT OrganizationMemberID 
                        FROM OrganizationMembers 
                        WHERE UserID = %s AND OrganizationID = %s
                    """, (user_id_binary, organization_id_binary))

                    if not await cur.fetchone():
                        raise HTTPException(status_code=404, detail="找不到該組織成員")

                    # 檢查是否為組織擁有者
                    await cur.execute("""
                        SELECT OwnerID 
                        FROM Organizations 
                        WHERE OrganizationID = %s AND OwnerID = %s
                    """, (organization_id_binary, user_id_binary))

                    if await cur.fetchone():
                        raise HTTPException(status_code=400, detail="無法刪除組織擁有者")

                    # 刪除用戶角色關聯
                    await cur.execute("""
                        DELETE FROM UserRoles 
                        WHERE UserID = %s AND OrganizationID = %s
                    """, (user_id_binary, organization_id_binary))

                    # 刪除組織成員關係
                    await cur.execute("""
                        DELETE FROM OrganizationMembers 
                        WHERE UserID = %s AND OrganizationID = %s
                    """, (user_id_binary, organization_id_binary))

                    # 更新用戶的組織ID為NULL
                    await cur.execute("""
                        UPDATE Users 
                        SET OrganizationID = NULL 
                        WHERE UserID = %s
                    """, (user_id_binary,))

                    await conn.commit()
                    return {"status": "success", "message": "成員已成功從組織中移除"}

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"刪除成員失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的ID格式")


# 取得資產內容(Content)
@app.post("/api/organizations/get_asset_content")
async def get_asset_content(data: dict):
    try:
        # 獲取必要參數
        asset_id = data.get("asset_id")
        organization_id = data.get("organization_id")

        if not all([asset_id, organization_id]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的ID轉換為BINARY(16)格式
        asset_id_binary = uuid.UUID(asset_id).bytes
        organization_id_binary = uuid.UUID(organization_id).bytes

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 檢查資產是否存在且屬於該組織
                    await cur.execute("""
                        SELECT 
                            AssetName,
                            AssetType,
                            Category,
                            Status,
                            Content,
                            UpdatedAt,
                            IsDeleted
                        FROM OrganizationAssets
                        WHERE AssetID = %s 
                        AND OrganizationID = %s
                        FOR UPDATE
                    """, (asset_id_binary, organization_id_binary))

                    asset = await cur.fetchone()
                    
                    if not asset:
                        raise HTTPException(status_code=404, detail="找不到該資產")
                    
                    # 檢查資產是否已刪除
                    if asset[6]:  # IsDeleted
                        raise HTTPException(status_code=400, detail="該資產已被刪除")

                    # 解析 JSON 內容
                    content = json.loads(asset[4]) if asset[4] else None

                    # 構建回應數據
                    response_data = {
                        "status": "success",
                        "data": {
                            "assetName": asset[0],
                            "assetType": asset[1],
                            "category": asset[2],
                            "status": asset[3],
                            "content": content,
                            "updatedAt": asset[5].isoformat() if asset[5] else None
                        }
                    }

                    await conn.commit()
                    return response_data

                except json.JSONDecodeError:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail="資產內容格式錯誤")
                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"獲取資產內容失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的ID格式")


# 檢查區塊權限的輔助函數
async def check_block_permission(
    cur,
    permissionChapter_id_binary: bytes,
    role_ids: list,
    asset_id: bytes
) -> bool:
    """
    檢查用戶是否有權限訪問指定的區塊
    
    Args:
        cur: 數據庫游標
        permissionChapter_id_binary: 章節權限識別標籤(UUID)
        role_ids: 用戶角色ID列表
        asset_id: 資產ID (UUID bytes)
        
    Returns:
        bool: 是否有權限
    """
    # 查詢該區塊的權限設置
    await cur.execute("""
        SELECT RoleID, ActionType
        FROM RolePermissionMappings
        WHERE PermissionChapterID = %s
        AND AssetID = %s
        FOR UPDATE
    """, (permissionChapter_id_binary, asset_id))
    
    permissions = await cur.fetchall()
    if not permissions:
        return False
    
    # 檢查用戶的角色是否有權限
    for role_id in role_ids:
        role_id_binary = uuid.UUID(role_id).bytes
        for permission in permissions:
            if permission[0] == role_id_binary and permission[1] in ['read', 'read_write']:
                return True
    
    return False


# 獲取區塊內容的輔助函數
async def get_block_content(
    cur,
    block_id: bytes,
    asset_id: bytes
) -> dict:
    """
    獲取區塊的內容和相關信息
    
    Args:
        cur: 數據庫游標
        block_id: 區塊ID (UUID bytes)
        asset_id: 資產ID (UUID bytes)
        
    Returns:
        dict: 區塊內容和相關信息
    """
    await cur.execute("""
        SELECT 
            content,
            LastModified,
            ModifiedBy,
            IsLocked,
            LockedBy,
            LockedAt,
            status
        FROM ReportContentBlocks
        WHERE BlockID = %s
        AND AssetID = %s
        FOR UPDATE
    """, (block_id, asset_id))
    
    block = await cur.fetchone()
    if not block:
        raise HTTPException(status_code=404, detail="找不到指定的區塊")
    
    # 獲取最後修改者的信息
    modified_by_info = None
    if block[2]:  # ModifiedBy
        await cur.execute("""
            SELECT UserName, AvatarUrl
            FROM Users
            WHERE UserID = %s
        """, (block[2],))
        modifier = await cur.fetchone()
        if modifier:
            modified_by_info = {
                "id": uuid.UUID(bytes=block[2]).hex,
                "name": modifier[0],
                "avatarUrl": modifier[1] or DEFAULT_USER_AVATAR
            }
    
    # 獲取鎖定者的信息
    locked_by_info = None
    if block[4]:  # LockedBy
        await cur.execute("""
            SELECT UserName, AvatarUrl
            FROM Users
            WHERE UserID = %s
        """, (block[4],))
        locker = await cur.fetchone()
        if locker:
            locked_by_info = {
                "id": uuid.UUID(bytes=block[4]).hex,
                "name": locker[0],
                "avatarUrl": locker[1] or DEFAULT_USER_AVATAR
            }
    
    return {
        "content": json.loads(block[0]) if block[0] else None,
        "lastModified": block[1].isoformat() if block[1] else None,
        "modifiedBy": modified_by_info,
        "isLocked": block[3],
        "lockedBy": locked_by_info,
        "lockedAt": block[5].isoformat() if block[5] else None,
        "status": block[6]
    }


# 鎖定區塊的輔助函數
async def lock_block(
    cur,
    block_id: bytes,
    user_id: bytes,
    asset_id: bytes
) -> None:
    """
    鎖定指定的區塊
    
    Args:
        cur: 數據庫游標
        block_id: 區塊ID (UUID bytes)
        user_id: 用戶ID (UUID bytes)
        asset_id: 資產ID (UUID bytes)
    """
    current_time = datetime.now(timezone.utc)
    await cur.execute("""
        UPDATE ReportContentBlocks
        SET IsLocked = TRUE,
            LockedBy = %s,
            LockedAt = %s
        WHERE BlockID = %s
        AND AssetID = %s
        AND (IsLocked = FALSE OR LockedAt < %s)
    """, (
        user_id,
        current_time,
        block_id,
        asset_id,
        current_time - timedelta(minutes=30)  # 自動解鎖30分鐘前的鎖定
    ))


# 解鎖區塊的輔助函數
async def unlock_block(cur, block_id: bytes, asset_id: bytes) -> None:
    """
    解鎖指定的區塊
    
    Args:
        cur: 數據庫游標
        block_id: 區塊ID (UUID bytes)
        asset_id: 資產ID (UUID bytes)
    """
    await cur.execute("""
        UPDATE ReportContentBlocks
        SET IsLocked = FALSE,
            LockedBy = NULL,
            LockedAt = NULL
        WHERE BlockID = %s
        AND AssetID = %s
    """, (block_id, asset_id))


# 取得公司基本表的區塊內容(Block)
@app.post("/api/organizations/get_company_table_blocks")
async def get_company_table_blocks(data: dict):
    """
    獲取公司基本表的區塊內容
    
    Args:
        data: 包含以下字段的字典：
            - blockID: 章節權限識別標籤(UUID)
            - asset_id: 資產ID(UUID)
            - user_id: 用戶ID(UUID)
            - roleID: 角色ID列表(JSON格式)
            - permissionChapter_id: 章節權限識別標籤(UUID)
            
    Returns:
        dict: 包含區塊內容和狀態信息的響應
    """
    try:
        # 參數驗證
        block_id = data.get("blockID")
        asset_id = data.get("asset_id")
        user_id = data.get("user_id")
        role_ids = data.get("roleID")
        permissionChapter_id = data.get("permissionChapter_id")
        
        if not all([block_id, asset_id, user_id, role_ids]):
            raise HTTPException(status_code=400, detail="缺少必要參數")
        
        # 將逗號分隔的字符串轉換為列表
        if isinstance(role_ids, str):
            role_ids = role_ids.split(',')
        
        if not isinstance(role_ids, list):
            raise HTTPException(status_code=400, detail="roleID 必須是列表")
        
        # 轉換 UUID 為二進制格式
        try:
            block_id_binary = uuid.UUID(block_id).bytes
            permissionChapter_id_binary = uuid.UUID(permissionChapter_id).bytes
            asset_id_binary = uuid.UUID(asset_id).bytes
            user_id_binary = uuid.UUID(user_id).bytes
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=f"無效的 UUID 格式: {str(ve)}")
        
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()
                    
                    # 檢查權限
                    has_permission = await check_block_permission(
                        cur, permissionChapter_id_binary, role_ids, asset_id_binary
                    )
                    
                    if not has_permission:
                        raise HTTPException(status_code=403, detail="權限不足")
                    
                    # 獲取區塊內容
                    block_data = await get_block_content(
                        cur, block_id_binary, asset_id_binary
                    )
                    
                    await conn.commit()

                    return {
                        "status": "success",
                        "data": block_data
                    }
                    
                except Exception as e:
                    await conn.rollback()
                    print(f"數據庫操作失敗: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"獲取區塊內容失敗: {str(e)}")
                    
    except HTTPException as e:
        print(f"HTTP異常: {str(e)}")
        raise e
    except Exception as e:
        print(f"未預期的錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 修改公司基本表的區塊內容
@app.post("/api/organizations/update_company_table_block")
async def update_company_table_block(data: dict):
    try:
        # 獲取必要參數
        block_id = data.get("block_id")
        asset_id = data.get("asset_id")
        user_id = data.get("user_id")
        content = data.get("content")
        
        if not all([block_id, asset_id, user_id, content]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的ID轉換為BINARY(16)格式
        block_id_binary = uuid.UUID(block_id).bytes
        asset_id_binary = uuid.UUID(asset_id).bytes
        user_id_binary = uuid.UUID(user_id).bytes

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 檢查區塊是否存在並獲取原始內容
                    await cur.execute("""
                        SELECT 
                            content,
                            IsLocked,
                            LockedBy
                        FROM ReportContentBlocks
                        WHERE BlockID = %s
                        AND AssetID = %s
                        FOR UPDATE
                    """, (block_id_binary, asset_id_binary))
                    
                    block = await cur.fetchone()
                    if not block:
                        raise HTTPException(status_code=404, detail="找不到指定的區塊")

                    # 檢查區塊是否被鎖定
                    is_locked, locked_by = block[1], block[2]
                    if is_locked and locked_by != user_id_binary:
                        raise HTTPException(status_code=403, detail="區塊已被其他用戶鎖定")

                    # 解析原始內容
                    try:
                        original_content = json.loads(block[0]) if block[0] else {}
                    except json.JSONDecodeError:
                        raise HTTPException(status_code=500, detail="區塊內容格式錯誤")

                    # 更新內容
                    original_content["content"]["text"] = content

                    # 更新區塊內容
                    current_time = datetime.now(timezone.utc)
                    await cur.execute("""
                        UPDATE ReportContentBlocks
                        SET content = %s,
                            LastModified = %s,
                            ModifiedBy = %s,
                            version = version + 1
                        WHERE BlockID = %s
                        AND AssetID = %s
                    """, (
                        json.dumps(original_content),
                        current_time,
                        user_id_binary,
                        block_id_binary,
                        asset_id_binary
                    ))

                    await conn.commit()
                    return {
                        "status": "success",
                        "message": "區塊內容已更新",
                        "data": {
                            "block_id": block_id,
                            "last_modified": current_time.isoformat(),
                            "version": "version + 1"
                        }
                    }

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"更新區塊內容失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的ID格式")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 鎖定區塊
@app.post("/api/organizations/lock_block")
async def lock_block_api(data: dict):
    try:
        # 獲取必要參數
        block_id = data.get("block_id")
        asset_id = data.get("asset_id")
        user_id = data.get("user_id")

        if not all([block_id, asset_id, user_id]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的ID轉換為BINARY(16)格式
        block_id_binary = uuid.UUID(block_id).bytes
        asset_id_binary = uuid.UUID(asset_id).bytes
        user_id_binary = uuid.UUID(user_id).bytes

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 檢查區塊是否存在
                    await cur.execute("""
                        SELECT IsLocked, LockedBy, LockedAt
                        FROM ReportContentBlocks
                        WHERE BlockID = %s AND AssetID = %s
                        FOR UPDATE
                    """, (block_id_binary, asset_id_binary))

                    block_data = await cur.fetchone()
                    if not block_data:
                        raise HTTPException(status_code=404, detail="找不到指定的區塊")

                    is_locked, locked_by, locked_at = block_data

                    # 檢查區塊是否已被鎖定
                    current_time = datetime.now(timezone.utc)
                    if is_locked:
                        # 如果鎖定時間超過30分鐘，自動解鎖
                        if locked_at and (current_time - locked_at) > timedelta(minutes=30):
                            is_locked = False
                        else:
                            # 如果是被同一用戶鎖定，允許繼續編輯
                            if locked_by != user_id_binary:
                                raise HTTPException(status_code=400, detail="區塊已被其他用戶鎖定")

                    # 鎖定區塊
                    await cur.execute("""
                        UPDATE ReportContentBlocks
                        SET IsLocked = TRUE,
                            LockedBy = %s,
                            LockedAt = %s
                        WHERE BlockID = %s AND AssetID = %s
                    """, (user_id_binary, current_time, block_id_binary, asset_id_binary))

                    await conn.commit()
                    return {
                        "status": "success",
                        "message": "區塊已成功鎖定"
                    }

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"鎖定區塊失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的ID格式")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 解鎖區塊
@app.post("/api/organizations/unlock_block")
async def unlock_block(data: dict):
    try:
        # 獲取必要參數
        block_id = data.get("block_id")
        asset_id = data.get("asset_id")
        user_id = data.get("user_id")

        if not all([block_id, asset_id, user_id]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的ID轉換為BINARY(16)格式
        block_id_binary = uuid.UUID(block_id).bytes
        asset_id_binary = uuid.UUID(asset_id).bytes
        user_id_binary = uuid.UUID(user_id).bytes

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 檢查區塊是否存在且被鎖定
                    await cur.execute("""
                        SELECT IsLocked, LockedBy
                        FROM ReportContentBlocks
                        WHERE BlockID = %s AND AssetID = %s
                        FOR UPDATE
                    """, (block_id_binary, asset_id_binary))
                    block_data = await cur.fetchone()
                    if not block_data:
                        raise HTTPException(status_code=404, detail="找不到指定的區塊")

                    is_locked, locked_by = block_data

                    # 檢查區塊是否已被鎖定，以及是否由當前用戶鎖定
                    if not is_locked:
                        raise HTTPException(status_code=400, detail="區塊未被鎖定")
                    if locked_by != user_id_binary:
                        raise HTTPException(status_code=403, detail="無權解鎖此區塊")

                    # 解鎖區塊
                    await cur.execute("""
                        UPDATE ReportContentBlocks
                        SET IsLocked = FALSE,
                            LockedBy = NULL,
                            LockedAt = NULL
                        WHERE BlockID = %s AND AssetID = %s
                    """, (block_id_binary, asset_id_binary))

                    await conn.commit()
                    return {
                        "status": "success",
                        "message": "區塊已成功解鎖"
                    }

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"解鎖區塊失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的ID格式")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 檢查頁面鎖定狀態
@app.post("/api/organizations/check_page_lock")
async def check_page_lock(data: dict):
    # 輸入 asset_id
    asset_id = data.get("asset_id")
    # 輸入 block_id 
    block_id = data.get("block_id")

    if not asset_id:
        raise HTTPException(status_code=400, detail="缺少必要參數 asset_id")

    try:
        # 將字符串格式的ID轉換為BINARY(16)格式
        asset_id_binary = uuid.UUID(asset_id).bytes
        block_id_binary = uuid.UUID(block_id).bytes if block_id else None

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 檢查區塊是否被鎖定
                    await cur.execute("""
                        SELECT IsLocked, LockedBy, 
                               (SELECT Username FROM Users WHERE UserID = LockedBy) as LockedByUsername,
                               (SELECT AvatarUrl FROM Users WHERE UserID = LockedBy) as LockedByAvatarUrl
                        FROM ReportContentBlocks 
                        WHERE AssetID = %s AND BlockID = %s
                    """, (asset_id_binary, block_id_binary))
                    
                    result = await cur.fetchone()
                    if not result:
                        return {
                            "status": "success",
                            "isLocked": False,
                            "lockedBy": None
                        }

                    is_locked, locked_by, locked_by_username, locked_by_avatar = result
                    
                    if is_locked and locked_by:
                        return {
                            "status": "success",
                            "isLocked": True,
                            "lockedBy": {
                                "id": str(uuid.UUID(bytes=locked_by)),
                                "name": locked_by_username,
                                "avatarUrl": locked_by_avatar
                            }
                        }
                    else:
                        return {
                            "status": "success",
                            "isLocked": False,
                            "lockedBy": None
                        }

                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"檢查鎖定狀態失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的ID格式")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 建立公司基本表
@app.post("/api/organizations/create_company_table")
async def create_company_table(data: dict):
    try:
        # 獲取必要參數
        company_name = data.get("company_name")  # 公司基本表的名稱
        creator_id = data.get("creator_id")      # 創建者ID
        organization_id = data.get("organization_id")  # 組織ID
        template_url = data.get("template_url")  # 模板URL
        category = data.get("category")  # 類別

        if not all([company_name, creator_id, organization_id, template_url, category]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的ID轉換為BINARY(16)格式
        creator_id_binary = uuid.UUID(creator_id).bytes
        organization_id_binary = uuid.UUID(organization_id).bytes

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 檢查組織是否存在
                    await cur.execute(
                        "SELECT OrganizationID FROM Organizations WHERE OrganizationID = %s AND IsDeleted = FALSE",
                        (organization_id_binary,)
                    )
                    if not await cur.fetchone():
                        raise HTTPException(status_code=404, detail="找不到指定的組織")

                    # 獲取模板內容
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(template_url, headers={
                            'Accept': 'application/json',
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }) as response:
                            if response.status != 200:
                                raise HTTPException(status_code=400, detail=f"無法獲取模板內容: HTTP {response.status}")
                            try:
                                template_data = await response.json(content_type=None)
                            except Exception as e:
                                raise HTTPException(status_code=400, detail=f"模板內容解析失敗: {str(e)}")

                    # 驗證模板格式
                    if not isinstance(template_data, dict) or "chapters" not in template_data:
                        raise HTTPException(status_code=400, detail="無效的模板格式")

                    # 生成資產ID
                    asset_id = uuid.uuid4().bytes

                    # 獲取組織中"一般"角色的RoleID
                    await cur.execute("""
                        SELECT RoleID 
                        FROM Roles 
                        WHERE OrganizationID = %s AND RoleName = '一般'
                    """, (organization_id_binary,))
                    general_role = await cur.fetchone()
                    if not general_role:
                        raise HTTPException(status_code=404, detail="找不到組織的一般角色")
                    general_role_id = general_role[0]

                    # 處理模板內容，為每個區塊生成新的UUID
                    processed_content = {"AssetID": uuid.UUID(bytes=asset_id).hex, "chapters": []}
                    blocks_to_create = []  # 儲存要創建的內容區塊
                    permissions_to_create = []  # 儲存要創建的權限映射

                    for chapter in template_data.get("chapters", []):
                        processed_chapter = {"chapterTitle": chapter["chapterTitle"], "subChapters": []}
                        for sub_chapter in chapter.get("subChapters", []):
                            processed_sub_chapter = {
                                "subChapterTitle": sub_chapter["subChapterTitle"],
                                "subSubChapters": []
                            }
                            for sub_sub_chapter in sub_chapter.get("subSubChapters", []):
                                # 為每個子章節生成唯一ID
                                block_id = uuid.uuid4().bytes
                                permission_id = uuid.uuid4().bytes

                                # 準備內容區塊數據
                                blocks_to_create.append((
                                    block_id,
                                    asset_id,
                                    'editing',
                                    json.dumps({
                                        "BlockID": uuid.UUID(bytes=block_id).hex,
                                        "subChapterTitle": sub_sub_chapter["subSubChapterTitle"],
                                        "content": {"text": ""}
                                    }),
                                    creator_id_binary
                                ))

                                # 準備權限映射數據
                                permissions_to_create.append((
                                    general_role_id,
                                    permission_id,
                                    asset_id,
                                    'company_info',
                                    'read_write'
                                ))

                                # 添加到處理後的內容中
                                processed_sub_chapter["subSubChapters"].append({
                                    "subSubChapterTitle": sub_sub_chapter["subSubChapterTitle"],
                                    "BlockID": uuid.UUID(bytes=block_id).hex,
                                    "access_permissions": uuid.UUID(bytes=permission_id).hex
                                })
                            processed_chapter["subChapters"].append(processed_sub_chapter)
                        processed_content["chapters"].append(processed_chapter)

                    # 首先創建組織資產記錄
                    await cur.execute("""
                        INSERT INTO OrganizationAssets (
                            AssetID, OrganizationID, AssetName, AssetType,
                            Category, CreatorID, Status, Content
                        ) VALUES (%s, %s, %s, 'company_info', %s, %s, 'editing', %s)
                    """, (
                        asset_id,
                        organization_id_binary,
                        company_name,
                        category,
                        creator_id_binary,
                        json.dumps(processed_content)
                    ))

                    # 然後批量創建內容區塊
                    for block_data in blocks_to_create:
                        await cur.execute("""
                            INSERT INTO ReportContentBlocks (
                                BlockID, AssetID, status, content, ModifiedBy
                            ) VALUES (%s, %s, %s, %s, %s)
                        """, block_data)

                    # 最後批量創建權限映射
                    for permission_data in permissions_to_create:
                        await cur.execute("""
                            INSERT INTO RolePermissionMappings (
                                RoleID, PermissionChapterID, AssetID, ResourceType, ActionType
                            ) VALUES (%s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                            ResourceType = VALUES(ResourceType),
                            ActionType = VALUES(ActionType)
                        """, permission_data)

                    await conn.commit()
                    return {
                        "status": "success",
                        "message": "公司基本表創建成功",
                        "data": {
                            "asset_id": uuid.UUID(bytes=asset_id).hex,
                            "content": processed_content
                        }
                    }

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"創建公司基本表失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的ID格式")


# 更新資產名稱
@app.post("/api/organizations/update_asset_name")
async def update_asset_name(data: dict):
    try:
        # 傳入資產ID、組織ID、新資產名稱
        asset_id = data.get("asset_id")
        organization_id = data.get("organization_id")
        new_asset_name = data.get("asset_name")

        if not all([asset_id, organization_id, new_asset_name]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 驗證資產名稱長度
        if len(new_asset_name) > 100:
            raise HTTPException(status_code=400, detail="資產名稱長度不能超過100個字符")

        # 將字符串格式的ID轉換為BINARY(16)格式
        asset_id_binary = uuid.UUID(asset_id).bytes
        organization_id_binary = uuid.UUID(organization_id).bytes

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 檢查資產是否存在且屬於該組織
                    await cur.execute("""
                        SELECT AssetID 
                        FROM OrganizationAssets 
                        WHERE AssetID = %s 
                        AND OrganizationID = %s 
                        AND IsDeleted = FALSE
                    """, (asset_id_binary, organization_id_binary))

                    if not await cur.fetchone():
                        raise HTTPException(status_code=404, detail="找不到該資產或資產已被刪除")

                    # 更新資產名稱
                    await cur.execute("""
                        UPDATE OrganizationAssets 
                        SET AssetName = %s,
                            UpdatedAt = CURRENT_TIMESTAMP
                        WHERE AssetID = %s 
                        AND OrganizationID = %s
                    """, (new_asset_name, asset_id_binary, organization_id_binary))

                    await conn.commit()
                    return {
                        "status": "success",
                        "message": "資產名稱更新成功",
                        "data": {
                            "asset_id": asset_id,
                            "new_asset_name": new_asset_name
                        }
                    }

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"更新資產名稱失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的ID格式")


# 刪除資產
@app.post("/api/organizations/delete_asset")
async def delete_asset(data: dict):
    try:
        # 從請求中獲取必要參數
        user_id = data.get("user_id")
        asset_id = data.get("asset_id")
        organization_id = data.get("organization_id")

        if not all([user_id, asset_id, organization_id]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 連接資料庫
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 檢查資產是否存在且屬於該組織
                query = """
                    SELECT AssetID 
                    FROM OrganizationAssets 
                    WHERE AssetID = UNHEX(REPLACE(%s, '-', ''))
                    AND OrganizationID = UNHEX(REPLACE(%s, '-', ''))
                    AND IsDeleted = FALSE
                """
                await cur.execute(query, (asset_id, organization_id))
                asset = await cur.fetchone()
                
                if not asset:
                    raise HTTPException(status_code=404, detail="找不到該資產或資產已被刪除")

                # 更新資產狀態
                update_query = """
                    UPDATE OrganizationAssets 
                    SET IsDeleted = TRUE,
                        DeletedAt = CURRENT_TIMESTAMP,
                        DeletedBy = UNHEX(REPLACE(%s, '-', ''))
                    WHERE AssetID = UNHEX(REPLACE(%s, '-', ''))
                """
                await cur.execute(update_query, (user_id, asset_id))
                await conn.commit()

        return {"message": "資產已成功刪除"}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除資產時發生錯誤: {str(e)}")


# 取得組織資產
@app.get("/api/organizations/get_organization_assets")
async def get_organization_assets(organization_id: str):
    try:
        # 獲取組織ID並轉換為BINARY(16)格式
        organization_id_bytes = uuid.UUID(organization_id).bytes
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="無效的組織ID格式")

    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # 開始事務
                await conn.begin()

                # 查詢組織的所有未刪除的資產
                await cur.execute("""
                    SELECT 
                        AssetID,
                        AssetName,
                        AssetType,
                        Status,
                        UpdatedAt,
                        CreatorID,
                        CreatedAt
                    FROM OrganizationAssets
                    WHERE OrganizationID = %s 
                    AND IsDeleted = FALSE
                    ORDER BY UpdatedAt DESC
                """, (organization_id_bytes,))

                assets = await cur.fetchall()
                
                # 格式化資產列表
                asset_list = []
                for asset in assets:
                    # 獲取創建者信息
                    creator_info = None
                    if asset[5]:  # 如果有創建者ID
                        await cur.execute("""
                            SELECT UserName, AvatarUrl
                            FROM Users
                            WHERE UserID = %s
                        """, (asset[5],))
                        creator = await cur.fetchone()
                        if creator:
                            creator_info = {
                                "id": uuid.UUID(bytes=asset[5]).hex,
                                "name": creator[0],
                                "avatarUrl": creator[1] or DEFAULT_USER_AVATAR
                            }

                    asset_list.append({
                        "assetID": uuid.UUID(bytes=asset[0]).hex,
                        "assetName": asset[1],
                        "assetType": asset[2],
                        "status": asset[3],
                        "updatedAt": asset[4].isoformat() if asset[4] else None,
                        "creator": creator_info,
                        "createdAt": asset[6].isoformat() if asset[6] else None
                    })

                await conn.commit()
                return {
                    "status": "success",
                    "data": asset_list
                }

            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"獲取組織資產失敗: {str(e)}")


# 建立準則模板
@app.post("/api/organizations/create_standard_template")
async def create_standard_template(data: dict):
    try:
        # 獲取必要參數
        organization_id = data.get("organization_id")
        creator_id = data.get("creator_id")
        template_name = data.get("template_name")
        category = data.get("category")

        if not all([organization_id, creator_id, template_name, category]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的ID轉換為BINARY(16)格式
        organization_id_binary = uuid.UUID(organization_id).bytes
        creator_id_binary = uuid.UUID(creator_id).bytes

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 檢查組織是否存在
                    await cur.execute("""
                        SELECT OrganizationID 
                        FROM Organizations 
                        WHERE OrganizationID = %s AND IsDeleted = FALSE
                    """, (organization_id_binary,))

                    if not await cur.fetchone():
                        raise HTTPException(status_code=404, detail="找不到指定的組織")

                    # 生成必要的 UUID
                    asset_id = uuid.uuid4().bytes
                    block_id = uuid.uuid4().bytes
                    permission_chapter_id = uuid.uuid4().bytes

                    # 獲取組織中"一般"角色的RoleID
                    await cur.execute("""
                        SELECT RoleID 
                        FROM Roles 
                        WHERE OrganizationID = %s AND RoleName = '一般'
                    """, (organization_id_binary,))
                    
                    general_role = await cur.fetchone()
                    if not general_role:
                        raise HTTPException(status_code=404, detail="找不到組織的一般角色")

                    # 準備資產內容
                    asset_content = {
                        "AssetID": uuid.UUID(bytes=asset_id).hex,
                        "BlockID": uuid.UUID(bytes=block_id).hex,
                        "access_permissions": uuid.UUID(bytes=permission_chapter_id).hex
                    }

                    # 1. 在 organizationassets 表中建立資料
                    await cur.execute("""
                        INSERT INTO OrganizationAssets (
                            AssetID,
                            OrganizationID,
                            AssetName,
                            AssetType,
                            Category,
                            CreatorID,
                            Status,
                            Content
                        ) VALUES (%s, %s, %s, 'standard_template', %s, %s, 'editing', %s)
                    """, (
                        asset_id,
                        organization_id_binary,
                        template_name,
                        category,
                        creator_id_binary,
                        json.dumps(asset_content)
                    ))

                    # 2. 在 rolepermissionmappings 表中建立資料
                    await cur.execute("""
                        INSERT INTO RolePermissionMappings (
                            RoleID,
                            PermissionChapterID,
                            AssetID,
                            ResourceType,
                            ActionType
                        ) VALUES (%s, %s, %s, 'standard_template', 'read_write')
                    """, (
                        general_role[0],  # 一般角色ID
                        permission_chapter_id,
                        asset_id
                    ))

                    # 3. 在 reportcontentblocks 表中建立資料
                    await cur.execute("""
                        INSERT INTO ReportContentBlocks (
                            BlockID,
                            AssetID,
                            status,
                            content,
                            ModifiedBy
                        ) VALUES (%s, %s, 'editing', %s, %s)
                    """, (
                        block_id,
                        asset_id,
                        json.dumps({"selectedCriteria": []}),  # 空的內容，表示剛建立還沒有選擇準則
                        creator_id_binary
                    ))

                    await conn.commit()
                    return {
                        "status": "success",
                        "message": "準則模板創建成功",
                        "data": {
                            "asset_id": uuid.UUID(bytes=asset_id).hex,
                            "block_id": uuid.UUID(bytes=block_id).hex,
                            "permission_chapter_id": uuid.UUID(bytes=permission_chapter_id).hex
                        }
                    }

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"創建準則模板失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的ID格式")


# 取得準則模板
@app.post("/api/organizations/get_standard_template")
async def get_standard_template(data: dict):
    try:
        # 獲取必要參數
        asset_id = data.get("asset_id")
        organization_id = data.get("organization_id")
        role_ids = data.get("role_ids") # 使用 , 分隔

        if not all([asset_id, organization_id, role_ids]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 確保 role_ids 是列表
        if isinstance(role_ids, str):
            role_ids = role_ids.split(',')
        if not isinstance(role_ids, list):
            raise HTTPException(status_code=400, detail="role_ids 必須是列表")

        # 將字符串格式的 ID 轉換為 BINARY(16) 格式
        try:
            asset_id_binary = uuid.UUID(asset_id).bytes
            organization_id_binary = uuid.UUID(organization_id).bytes
        except ValueError:
            raise HTTPException(status_code=400, detail="無效的ID格式")

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 從 organizationassets 表獲取資產資訊
                    await cur.execute("""
                        SELECT 
                            AssetName,
                            AssetType,
                            Category,
                            Status,
                            Content,
                            IsDeleted
                        FROM OrganizationAssets
                        WHERE AssetID = %s
                        AND OrganizationID = %s
                        FOR UPDATE
                    """, (asset_id_binary, organization_id_binary))

                    asset = await cur.fetchone()
                    if not asset:
                        raise HTTPException(status_code=404, detail="找不到該資產")

                    # 檢查資產是否已被刪除
                    if asset[5]:  # IsDeleted
                        raise HTTPException(status_code=404, detail="該資產已被刪除")

                    # 解析資產內容以獲取 BlockID 和 access_permissions
                    try:
                        content = json.loads(asset[4]) if asset[4] else {}
                        block_id = content.get("BlockID")
                        access_permissions = content.get("access_permissions")

                        if not all([block_id, access_permissions]):
                            raise HTTPException(status_code=400, detail="資產內容格式錯誤")

                        # 將字符串格式的 ID 轉換為 BINARY(16)
                        block_id_binary = uuid.UUID(block_id).bytes
                        permission_id_binary = uuid.UUID(access_permissions).bytes

                    except (json.JSONDecodeError, ValueError) as e:
                        raise HTTPException(status_code=400, detail="資產內容解析失敗")

                    # 驗證權限
                    has_permission = await check_block_permission(
                        cur, permission_id_binary, role_ids, asset_id_binary
                    )
                    
                    if not has_permission:
                        raise HTTPException(status_code=403, detail="權限不足")

                    # 從 reportcontentblocks 表獲取區塊內容
                    await cur.execute("""
                        SELECT 
                            content,
                            LastModified,
                            ModifiedBy,
                            IsLocked,
                            LockedBy,
                            LockedAt,
                            status
                        FROM ReportContentBlocks
                        WHERE BlockID = %s AND AssetID = %s
                        FOR UPDATE
                    """, (block_id_binary, asset_id_binary))

                    block = await cur.fetchone()
                    if not block:
                        raise HTTPException(status_code=404, detail="找不到區塊內容")

                    # 獲取最後修改者的信息
                    modified_by_info = None
                    if block[2]:  # ModifiedBy
                        await cur.execute("""
                            SELECT UserName, AvatarUrl
                            FROM Users
                            WHERE UserID = %s
                        """, (block[2],))
                        modifier = await cur.fetchone()
                        if modifier:
                            modified_by_info = {
                                "id": uuid.UUID(bytes=block[2]).hex,
                                "name": modifier[0],
                                "avatarUrl": modifier[1] or DEFAULT_USER_AVATAR
                            }

                    # 獲取鎖定者的信息
                    locked_by_info = None
                    if block[4]:  # LockedBy
                        await cur.execute("""
                            SELECT UserName, AvatarUrl
                            FROM Users
                            WHERE UserID = %s
                        """, (block[4],))
                        locker = await cur.fetchone()
                        if locker:
                            locked_by_info = {
                                "id": uuid.UUID(bytes=block[4]).hex,
                                "name": locker[0],
                                "avatarUrl": locker[1] or DEFAULT_USER_AVATAR
                            }

                    # 構建回應數據
                    response_data = {
                        "status": "success",
                        "data": {
                            "assetName": asset[0],
                            "assetType": asset[1],
                            "category": asset[2],
                            "status": asset[3],
                            "content": json.loads(block[0]) if block[0] else None,
                            "lastModified": block[1].isoformat() if block[1] else None,
                            "modifiedBy": modified_by_info,
                            "isLocked": block[3],
                            "lockedBy": locked_by_info,
                            "lockedAt": block[5].isoformat() if block[5] else None,
                            "blockStatus": block[6],
                            "block_id": block_id,
                            "PermissionChapterID": access_permissions
                        }
                    }

                    await conn.commit()
                    return response_data

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"獲取準則模板失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的ID格式")


# 儲存準則模板
@app.post("/api/organizations/save_standard_template")
async def save_standard_template(data: dict):
    try:
        # 獲取必要參數
        asset_id = data.get("asset_id")
        organization_id = data.get("organization_id")
        asset_name = data.get("asset_name")
        block_id = data.get("block_id")
        permission_chapter_id = data.get("permission_chapter_id")
        role_ids = data.get("role_ids")
        selected_criteria = data.get("selected_criteria")
        user_id = data.get("user_id")  # 用於記錄修改者

        if not all([asset_id, organization_id, block_id, permission_chapter_id, role_ids, selected_criteria, user_id]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 確保 role_ids 是列表
        if isinstance(role_ids, str):
            role_ids = role_ids.split(',')
        if not isinstance(role_ids, list):
            raise HTTPException(status_code=400, detail="role_ids 必須是列表")

        # 將字符串格式的ID轉換為BINARY(16)格式
        try:
            asset_id_binary = uuid.UUID(asset_id).bytes
            organization_id_binary = uuid.UUID(organization_id).bytes
            block_id_binary = uuid.UUID(block_id).bytes
            permission_chapter_id_binary = uuid.UUID(permission_chapter_id).bytes
            user_id_binary = uuid.UUID(user_id).bytes
        except ValueError:
            raise HTTPException(status_code=400, detail="無效的ID格式")

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 檢查權限
                    has_permission = await check_block_permission(
                        cur, permission_chapter_id_binary, role_ids, asset_id_binary
                    )
                    if not has_permission:
                        raise HTTPException(status_code=403, detail="權限不足")

                    # 檢查資產是否存在且屬於該組織
                    await cur.execute("""
                        SELECT AssetID 
                        FROM OrganizationAssets 
                        WHERE AssetID = %s 
                        AND OrganizationID = %s 
                        AND IsDeleted = FALSE
                        FOR UPDATE
                    """, (asset_id_binary, organization_id_binary))

                    if not await cur.fetchone():
                        raise HTTPException(status_code=404, detail="找不到該資產或資產已被刪除")

                    # 檢查區塊是否被鎖定
                    await cur.execute("""
                        SELECT IsLocked, LockedBy
                        FROM ReportContentBlocks
                        WHERE BlockID = %s AND AssetID = %s
                        FOR UPDATE
                    """, (block_id_binary, asset_id_binary))

                    block_status = await cur.fetchone()
                    if not block_status:
                        raise HTTPException(status_code=404, detail="找不到指定的區塊")

                    is_locked, locked_by = block_status
                    if is_locked and locked_by != user_id_binary:
                        raise HTTPException(status_code=403, detail="區塊已被其他用戶鎖定")

                    # 更新資產名稱（如果提供）
                    if asset_name:
                        await cur.execute("""
                            UPDATE OrganizationAssets 
                            SET AssetName = %s,
                                UpdatedAt = CURRENT_TIMESTAMP
                            WHERE AssetID = %s
                        """, (asset_name, asset_id_binary))

                    # 準備區塊內容
                    block_content = {
                        "BlockID": block_id,
                        "selectedCriteria": selected_criteria
                    }

                    # 更新區塊內容
                    current_time = datetime.now(timezone.utc)
                    await cur.execute("""
                        UPDATE ReportContentBlocks
                        SET content = %s,
                            LastModified = %s,
                            ModifiedBy = %s,
                            version = version + 1
                        WHERE BlockID = %s AND AssetID = %s
                    """, (
                        json.dumps(block_content),
                        current_time,
                        user_id_binary,
                        block_id_binary,
                        asset_id_binary
                    ))

                    await conn.commit()
                    return {
                        "status": "success",
                        "message": "準則模板保存成功",
                        "data": {
                            "asset_id": asset_id,
                            "block_id": block_id,
                            "last_modified": current_time.isoformat()
                        }
                    }

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"保存準則模板失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的ID格式")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 取得組織資產Modal
@app.post("/api/organizations/get_organization_assets_for_modal")
async def get_organization_assets_for_modal(data: dict):
    try:
        # 獲取組織ID
        organization_id = data.get("organization_id")
        if not organization_id:
            raise HTTPException(status_code=400, detail="缺少組織ID")

        # 將字符串格式的organization_id轉換為BINARY(16)格式
        organization_id_binary = uuid.UUID(organization_id).bytes

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 查詢組織的所有未刪除的資產
                    await cur.execute("""
                        SELECT 
                            AssetID,
                            AssetName,
                            AssetType,
                            Category,
                            Status,
                            CreatedAt,
                            UpdatedAt
                        FROM OrganizationAssets
                        WHERE OrganizationID = %s 
                        AND IsDeleted = FALSE
                        ORDER BY UpdatedAt DESC
                    """, (organization_id_binary,))

                    assets = await cur.fetchall()
                    
                    # 初始化分類結果
                    result = {
                        "standard_template": [],
                        "company_info": []
                    }

                    # 處理資產數據並分類
                    for asset in assets:
                        asset_data = {
                            "assetID": uuid.UUID(bytes=asset[0]).hex,
                            "assetName": asset[1],
                            "category": asset[3],
                            "status": asset[4],
                            "createdAt": asset[5].isoformat() if asset[5] else None,
                            "updatedAt": asset[6].isoformat() if asset[6] else None
                        }

                        # 根據資產類型分類
                        if asset[2] == 'standard_template':
                            result["standard_template"].append(asset_data)
                        elif asset[2] == 'company_info':
                            result["company_info"].append(asset_data)

                    await conn.commit()
                    return {
                        "status": "success",
                        "data": result
                    }

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"獲取組織資產失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的組織ID格式")


# 創建報告書
@app.post("/api/organizations/create_report")
async def create_report(data: dict):
    try:
        # 驗證必要參數是否存在
        print("data", data)
        required_fields = ['OrganizationID', 'AssetName', 'Category', 'CreatorID', 'company_info_assetID', 'standard_template_id']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"缺少必要参数: {field}")

        # 將UUID字符串轉換為二進制格式
        organization_id = uuid.UUID(data['OrganizationID']).bytes
        creator_id = uuid.UUID(data['CreatorID']).bytes
        company_info_asset_id = uuid.UUID(data['company_info_assetID']).bytes
        standard_template_id = uuid.UUID(data['standard_template_id']).bytes

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()
                    
                    # 驗證組織ID是否存在
                    await cur.execute(
                        "SELECT 1 FROM Organizations WHERE OrganizationID = %s AND IsDeleted = FALSE",
                        (organization_id,)
                    )
                    if not await cur.fetchone():
                        raise HTTPException(status_code=404, detail="组织不存在")

                    # 獲取公司基本資料的章節結構
                    await cur.execute(
                        "SELECT Content FROM OrganizationAssets WHERE AssetID = %s AND AssetType = 'company_info'",
                        (company_info_asset_id,)
                    )
                    company_info = await cur.fetchone()
                    if not company_info:
                        raise HTTPException(status_code=404, detail="公司基本资料不存在")

                    company_info_content = json.loads(company_info[0])
                    
                    # 創建新的報告書資產
                    new_asset_id = uuid.uuid4().bytes
                    new_chapters = []
                    
                    # 根據公司基本資料的章節結構創建報告書章節
                    for chapter in company_info_content['chapters']:
                        new_chapter = {
                            'chapterTitle': chapter['chapterTitle'],
                            'subChapters': []
                        }
                        
                        for sub_chapter in chapter['subChapters']:
                            # 為每個子章節創建新的BlockID和權限標識
                            block_id = uuid.uuid4().bytes
                            permission_id = uuid.uuid4().bytes
                            
                            new_sub_chapter = {
                                'subChapterTitle': sub_chapter['subChapterTitle'],
                                'BlockID': block_id.hex(),
                                'access_permissions': permission_id.hex()
                            }
                            
                            new_chapter['subChapters'].append(new_sub_chapter)
                        
                        new_chapters.append(new_chapter)

                    # 首先創建報告書資產
                    report_content = {
                        'company_info_assetID': data['company_info_assetID'],
                        'standard_template_id': data['standard_template_id'],
                        'chapters': new_chapters
                    }

                    await cur.execute(
                        """
                        INSERT INTO OrganizationAssets 
                        (AssetID, OrganizationID, AssetName, AssetType, Category, CreatorID, Content)
                        VALUES (%s, %s, %s, 'report', %s, %s, %s)
                        """,
                        (
                            new_asset_id,
                            organization_id,
                            data['AssetName'],
                            data['Category'],
                            creator_id,
                            json.dumps(report_content)
                        )
                    )

                    # 然後創建內容塊和權限映射
                    for chapter in new_chapters:
                        for sub_chapter in chapter['subChapters']:
                            block_id = uuid.UUID(sub_chapter['BlockID']).bytes
                            permission_id = uuid.UUID(sub_chapter['access_permissions']).bytes
                            
                            # 創建內容塊
                            await cur.execute(
                                """
                                INSERT INTO ReportContentBlocks 
                                (BlockID, AssetID, content) 
                                VALUES (%s, %s, %s)
                                """,
                                (
                                    block_id,
                                    new_asset_id,
                                    json.dumps({
                                        'BlockID': sub_chapter['BlockID'],
                                        'subChapterTitle': sub_chapter['subChapterTitle'],
                                        'content': {
                                            'text': '',
                                            'images': [],
                                            'guidelines': {},
                                            'comments': []
                                        }
                                    })
                                )
                            )
                            
                            # 創建默認權限映射
                            await cur.execute(
                                """
                                INSERT INTO RolePermissionMappings 
                                (RoleID, PermissionChapterID, AssetID, ResourceType, ActionType)
                                SELECT RoleID, %s, %s, 'report', 'read_write'
                                FROM Roles 
                                WHERE OrganizationID = %s AND RoleName = '一般'
                                """,
                                (permission_id, new_asset_id, organization_id)
                            )

                    await conn.commit()

                    # 新增報告書_公司資料_對應表
                    await cur.execute(
                        "INSERT INTO `reportcompanyinfomapping` (`MappingID`, `ReportID`, `CompanyInfoID`, `CreatedAt`) VALUES (NULL, %s, %s, current_timestamp())",
                        (new_asset_id, company_info_asset_id)
                    )

                    # 提交事務
                    await conn.commit()

                    return {
                        "status": "success",
                        "message": "報告書創建成功",
                        "data": {
                            "AssetID": new_asset_id.hex(),
                            "AssetName": data['AssetName']
                        }
                    }
                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"創建報告書失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"無效的UUID格式: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"創建報告書失敗: {str(e)}")


# 取得報告書大綱
@app.post("/api/report/get_report_data")
async def get_report_data(data: dict):
    try:
        # 獲取必要參數
        asset_id = data.get("asset_id")
        organization_id = data.get("organization_id")

        if not all([asset_id, organization_id]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的ID轉換為BINARY(16)格式
        try:
            asset_id_binary = uuid.UUID(asset_id).bytes
            organization_id_binary = uuid.UUID(organization_id).bytes
        except ValueError:
            raise HTTPException(status_code=400, detail="無效的ID格式")

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 查詢資產基本信息
                    await cur.execute("""
                        SELECT 
                            AssetName,
                            AssetType,
                            Category,
                            Status,
                            UpdatedAt,
                            Content,
                            CreatorID,
                            CreatedAt
                        FROM OrganizationAssets
                        WHERE AssetID = %s 
                        AND OrganizationID = %s 
                        AND IsDeleted = FALSE
                        AND AssetType = 'report'
                        FOR UPDATE
                    """, (asset_id_binary, organization_id_binary))

                    asset = await cur.fetchone()
                    if not asset:
                        raise HTTPException(status_code=404, detail="找不到該報告書或報告書已被刪除")

                    # 獲取創建者信息
                    creator_info = None
                    if asset[6]:  # CreatorID
                        await cur.execute("""
                            SELECT UserName, AvatarUrl
                            FROM Users
                            WHERE UserID = %s
                        """, (asset[6],))
                        creator = await cur.fetchone()
                        if creator:
                            creator_info = {
                                "id": uuid.UUID(bytes=asset[6]).hex,
                                "name": creator[0],
                                "avatarUrl": creator[1] or DEFAULT_USER_AVATAR
                            }

                    # 解析報告書內容
                    content = json.loads(asset[5]) if asset[5] else {}

                    # 獲取關聯的公司基本表和準則模板的資訊
                    company_info = None
                    standard_template = None

                    if 'company_info_assetID' in content:
                        company_info_id = uuid.UUID(content['company_info_assetID']).bytes
                        await cur.execute("""
                            SELECT AssetName, Category
                            FROM OrganizationAssets
                            WHERE AssetID = %s AND AssetType = 'company_info'
                        """, (company_info_id,))
                        company_info_data = await cur.fetchone()
                        if company_info_data:
                            company_info = {
                                "id": content['company_info_assetID'],
                                "name": company_info_data[0],
                                "category": company_info_data[1]
                            }

                    if 'standard_template_id' in content:
                        template_id = uuid.UUID(content['standard_template_id']).bytes
                        await cur.execute("""
                            SELECT AssetName, Category
                            FROM OrganizationAssets
                            WHERE AssetID = %s AND AssetType = 'standard_template'
                        """, (template_id,))
                        template_data = await cur.fetchone()
                        if template_data:
                            standard_template = {
                                "id": content['standard_template_id'],
                                "name": template_data[0],
                                "category": template_data[1]
                            }

                    # 構建回應數據
                    response_data = {
                        "status": "success",
                        "data": {
                            "company_info_assetID": content['company_info_assetID'],
                            "standard_template_id": content['standard_template_id'],
                            "assetName": asset[0],
                            "assetType": asset[1],
                            "category": asset[2],
                            "status": asset[3],
                            "updatedAt": asset[4].isoformat() if asset[4] else None,
                            "creator": creator_info,
                            "createdAt": asset[7].isoformat() if asset[7] else None,
                            "content": content,
                            "companyInfo": company_info,
                            "standardTemplate": standard_template
                        }
                    }

                    await conn.commit()
                    return response_data

                except json.JSONDecodeError:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail="報告書內容格式錯誤")
                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"獲取報告書資料失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的ID格式")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 取得報告書Block內容
@app.post("/api/report/get_report_block_data")
async def get_report_block_data(data: dict):
    try:
        # 獲取必要參數
        block_id = data.get("block_id")
        if not block_id:
            raise HTTPException(status_code=400, detail="缺少必要參數 block_id")

        # 將字符串格式的ID轉換為BINARY(16)格式
        try:
            block_id_binary = uuid.UUID(block_id).bytes
        except ValueError:
            raise HTTPException(status_code=400, detail="無效的區塊ID格式")

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 查詢區塊內容和相關信息
                    await cur.execute("""
                        SELECT 
                            content,
                            LastModified,
                            ModifiedBy,
                            IsLocked,
                            LockedBy,
                            LockedAt,
                            status,
                            AssetID
                        FROM ReportContentBlocks
                        WHERE BlockID = %s
                        FOR UPDATE
                    """, (block_id_binary,))

                    block = await cur.fetchone()
                    if not block:
                        raise HTTPException(status_code=404, detail="找不到指定的區塊")

                    # 獲取最後修改者的信息
                    modified_by_info = None
                    if block[2]:  # ModifiedBy
                        await cur.execute("""
                            SELECT UserName, AvatarUrl
                            FROM Users
                            WHERE UserID = %s
                        """, (block[2],))
                        modifier = await cur.fetchone()
                        if modifier:
                            modified_by_info = {
                                "id": uuid.UUID(bytes=block[2]).hex,
                                "name": modifier[0],
                                "avatarUrl": modifier[1] or DEFAULT_USER_AVATAR
                            }

                    # 獲取鎖定者的信息
                    locked_by_info = None
                    if block[4]:  # LockedBy
                        await cur.execute("""
                            SELECT UserName, AvatarUrl
                            FROM Users
                            WHERE UserID = %s
                        """, (block[4],))
                        locker = await cur.fetchone()
                        if locker:
                            locked_by_info = {
                                "id": uuid.UUID(bytes=block[4]).hex,
                                "name": locker[0],
                                "avatarUrl": locker[1] or DEFAULT_USER_AVATAR
                            }

                    # 構建回應數據
                    response_data = {
                        "status": "success",
                        "data": {
                            "blockID": block_id,
                            "assetID": uuid.UUID(bytes=block[7]).hex if block[7] else None,
                            "content": json.loads(block[0]) if block[0] else None,
                            "lastModified": block[1].isoformat() if block[1] else None,
                            "modifiedBy": modified_by_info,
                            "isLocked": block[3],
                            "lockedBy": locked_by_info,
                            "lockedAt": block[5].isoformat() if block[5] else None,
                            "blockStatus": block[6]
                        }
                    }

                    await conn.commit()
                    return response_data

                except json.JSONDecodeError:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail="區塊內容格式錯誤")
                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"獲取區塊內容失敗: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="無效的ID格式")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 更新報告書Block內容
@app.post("/api/report/update_report_block_data")
async def update_report_block_data(data: dict):
    try:
        block_id = data.get("block_id")
        content = data.get("content")
        user_id = data.get("user_id")

        if not all([block_id, content, user_id]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        try:
            block_id_binary = uuid.UUID(block_id).bytes
            user_id_binary = uuid.UUID(user_id).bytes
        except ValueError:
            raise HTTPException(status_code=400, detail="無效的ID格式")

        # 驗證內容格式
        try:
            if isinstance(content, str):
                content = json.loads(content)
            elif not isinstance(content, dict):
                raise ValueError("內容必須是JSON格式")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="內容必須是有效的JSON格式")

        # 使用全局的 db_pool
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 檢查區塊是否被鎖定
                await cur.execute("""
                    SELECT IsLocked, LockedBy, AssetID
                    FROM ReportContentBlocks
                    WHERE BlockID = %s
                """, (block_id_binary,))
                
                block_info = await cur.fetchone()
                if not block_info:
                    raise HTTPException(status_code=404, detail="找不到指定的區塊")
                
                is_locked, locked_by, asset_id = block_info

                if is_locked and locked_by != user_id_binary:
                    raise HTTPException(status_code=403, detail="該區塊已被其他用戶鎖定")

                # 檢查用戶是否有權限編輯該區塊
                await cur.execute("""
                    SELECT r.RoleID
                    FROM UserRoles ur
                    JOIN Roles r ON ur.RoleID = r.RoleID
                    WHERE ur.UserID = %s AND ur.OrganizationID = (
                        SELECT OrganizationID 
                        FROM OrganizationAssets 
                        WHERE AssetID = %s
                    )
                """, (user_id_binary, asset_id))
                
                user_roles = await cur.fetchall()
                if not user_roles:
                    raise HTTPException(status_code=403, detail="您沒有權限編輯此區塊")

                # 更新區塊內容
                try:
                    await cur.execute("""
                        UPDATE ReportContentBlocks
                        SET content = %s,
                            LastModified = CURRENT_TIMESTAMP(6),
                            ModifiedBy = %s,
                            version = version + 1
                        WHERE BlockID = %s
                    """, (json.dumps(content), user_id_binary, block_id_binary))

                    await conn.commit()
                    return {"status": "success", "message": "區塊內容已更新"}

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"更新區塊內容失敗: {str(e)}")

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


import os
import base64
import time
# 將 base64 的圖片存成圖片
def convert_base64_to_url(base64_string, output_dir="images", filename=None):
    """將 base64 的圖片存成圖片

    Args:
        base64_string: base64 編碼的圖片字串。
        output_dir: 圖片儲存的目錄，預設為 "images"。
        filename: 圖片的檔案名稱，如果為 None，則自動產生檔名。

    Returns:
        str: 圖片檔案的路徑 (包含檔名)。如果儲存失敗則返回 None。
    """
    try:
        # 檢查輸出目錄是否存在，不存在則創建
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 移除 base64 字串可能的前綴 (例如： "data:image/png;base64,")
        if ',' in base64_string:
            header, base64_string = base64_string.split(',', 1)
            image_format = header.split('/')[1].split(';')[0] # 嘗試從 header 取得圖片格式
        else:
            image_format = "png" # 預設圖片格式，如果無法從 header 判斷

        # 解碼 base64 字串
        image_data = base64.b64decode(base64_string)

        # 產生檔案名稱
        if filename is None:
            timestamp = int(time.time())
            filename = f"image_{timestamp}.{image_format}"
        elif '.' not in filename: # 確保檔名有副檔名
            filename = f"{filename}.{image_format}"

        filepath = os.path.join(output_dir, filename)

        # 儲存圖片
        with open(filepath, 'wb') as f:
            f.write(image_data)

        return "http://localhost:8001/" + filepath

    except Exception as e:
        print(f"儲存圖片失敗: {e}")
        return None


# api base64 轉 URL
@app.post("/api/base64_to_url")
async def base64_to_url(data: dict):
    base64_string = data.get("base64_string")
    return convert_base64_to_url(base64_string).replace("\\", "/")


# 更新報告書大綱(拖曳順序)
@app.post("/api/report/update_report_outline")
async def update_report_outline(data: dict):
    try:
        # 獲取必要參數
        asset_id = data.get("asset_id")
        content = data.get("content")

        if not all([asset_id, content]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 驗證內容格式
        try:
            if isinstance(content, str):
                content = json.loads(content)
            elif not isinstance(content, dict):
                raise ValueError("內容必須是JSON格式")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="內容必須是有效的JSON格式")

        # 將字符串格式的ID轉換為BINARY(16)格式
        try:
            asset_id_binary = uuid.UUID(asset_id).bytes
        except ValueError:
            raise HTTPException(status_code=400, detail="無效的資產ID格式")

        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 檢查資產是否存在且未被刪除
                    await cur.execute("""
                        SELECT AssetID 
                        FROM OrganizationAssets 
                        WHERE AssetID = %s 
                        AND IsDeleted = FALSE
                        FOR UPDATE
                    """, (asset_id_binary,))

                    if not await cur.fetchone():
                        raise HTTPException(status_code=404, detail="找不到該資產或資產已被刪除")

                    # 更新資產內容和更新時間
                    current_time = datetime.now(timezone.utc)
                    await cur.execute("""
                        UPDATE OrganizationAssets 
                        SET Content = %s,
                            UpdatedAt = %s
                        WHERE AssetID = %s
                    """, (json.dumps(content), current_time, asset_id_binary))

                    await conn.commit()
                    return {
                        "status": "success",
                        "message": "報告書大綱更新成功",
                        "data": {
                            "asset_id": asset_id,
                            "updated_at": current_time.isoformat()
                        }
                    }

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"更新報告書大綱失敗: {str(e)}")

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 更新報告書大綱(新增報告書章節標題)
@app.post("/api/report/update_report_outline_add_chapter_title")
async def update_report_outline_add_chapter_title(data: dict):
    try:
        # 檢查必要的參數
        if not all(key in data for key in ['asset_id', 'chapterTitle']):
            raise HTTPException(status_code=400, detail="缺少必要的參數")

        asset_id = data['asset_id']
        chapter_title = data['chapterTitle']

        # 轉換 UUID 字串為二進制格式
        try:
            asset_id_binary = uuid.UUID(asset_id).bytes
        except ValueError:
            raise HTTPException(status_code=400, detail="無效的 UUID 格式")

        # 修正非同步調用
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 檢查資產是否存在
                await cur.execute(
                    "SELECT Content FROM OrganizationAssets WHERE AssetID = %s AND IsDeleted = FALSE",
                    (asset_id_binary,)
                )
                result = await cur.fetchone()
                
                if not result:
                    raise HTTPException(status_code=404, detail="找不到指定的資產")
                
                try:
                    content = json.loads(result[0]) if result[0] else {"chapters": []}
                except json.JSONDecodeError:
                    content = {"chapters": []}

                # 新增章節標題
                new_chapter = {
                    "chapterTitle": chapter_title,
                    "subChapters": []
                }
                
                if "chapters" not in content:
                    content["chapters"] = []
                
                content["chapters"].append(new_chapter)

                # 更新資料庫
                current_time = datetime.now()
                try:
                    await cur.execute(
                        """
                        UPDATE OrganizationAssets 
                        SET Content = %s, UpdatedAt = %s 
                        WHERE AssetID = %s
                        """,
                        (json.dumps(content), current_time, asset_id_binary)
                    )
                    await conn.commit()

                    return {
                        "status": "success",
                        "message": "章節標題新增成功",
                        "data": {
                            "asset_id": asset_id,
                            "updated_at": current_time.isoformat()
                        }
                    }

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"更新資料失敗: {str(e)}")

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 更新報告書大綱(大章節)名稱
@app.post("/api/report/rename_chapter_title")
async def rename_chapter_title(data: dict):
    try:
        # 檢查必要參數
        if not all(key in data for key in ["asset_id", "chapter_title", "new_chapter_title"]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        asset_id = data["asset_id"]
        chapter_title = data["chapter_title"]
        new_chapter_title = data["new_chapter_title"]

        # 將 asset_id 轉換為 bytes
        try:
            asset_id_binary = uuid.UUID(asset_id).bytes
        except ValueError:
            raise HTTPException(status_code=400, detail="無效的 asset_id 格式")

        # 獲取資料庫連接
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 從資料庫獲取資產內容
                await cur.execute("""
                    SELECT Content 
                    FROM OrganizationAssets 
                    WHERE AssetID = %s AND IsDeleted = FALSE
                """, (asset_id_binary,))
                
                result = await cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="找不到指定的資產")

                content = json.loads(result[0]) if result[0] else {}
                
                # 檢查並更新章節標題
                if "chapters" not in content:
                    raise HTTPException(status_code=400, detail="資產內容格式錯誤")

                title_found = False
                for chapter in content["chapters"]:
                    if chapter.get("chapterTitle") == chapter_title:
                        chapter["chapterTitle"] = new_chapter_title
                        title_found = True
                        break

                if not title_found:
                    raise HTTPException(status_code=404, detail="找不到指定的章節標題")

                # 更新資料庫
                current_time = datetime.now()
                await cur.execute("""
                    UPDATE OrganizationAssets 
                    SET Content = %s, UpdatedAt = %s
                    WHERE AssetID = %s
                """, (json.dumps(content), current_time, asset_id_binary))

                await conn.commit()

                return {
                    "status": "success",
                    "message": "章節標題更新成功",
                    "data": {
                        "asset_id": asset_id,
                        "updated_at": current_time.isoformat()
                    }
                }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 刪除報告書大綱
@app.post("/api/report/delete_report_outline")
async def delete_report_outline(data: dict):
    try:
        asset_id = data.get("asset_id")
        chapter_title = data.get("chapterTitle")

        if not asset_id or not chapter_title:
            raise HTTPException(status_code=400, detail="缺少必要參數")

        asset_id_binary = uuid.UUID(asset_id).bytes

        # 獲取資料庫連接
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                    # 獲取資產內容
                    await cur.execute("""
                        SELECT Content 
                        FROM OrganizationAssets 
                        WHERE AssetID = %s AND IsDeleted = FALSE
                    """, (asset_id_binary,))
                    
                    result = await cur.fetchone()
                    if not result:
                        raise HTTPException(status_code=404, detail="找不到指定的資產")

                    content = json.loads(result[0])
                    if not content.get("chapters"):
                        raise HTTPException(status_code=400, detail="資產內容格式錯誤")

                    # 找到要刪除的章節
                    block_ids_to_delete = []
                    permission_ids_to_delete = []
                    new_chapters = []
                    chapter_found = False

                    for chapter in content["chapters"]:
                        if chapter["chapterTitle"] == chapter_title:
                            chapter_found = True
                            # 收集所有需要刪除的 BlockID 和 access_permissions
                            for subchapter in chapter["subChapters"]:
                                if subchapter.get("BlockID"):
                                    block_ids_to_delete.append(uuid.UUID(subchapter["BlockID"]).bytes)
                                if subchapter.get("access_permissions"):
                                    permission_ids_to_delete.append(uuid.UUID(subchapter["access_permissions"]).bytes)
                        else:
                            new_chapters.append(chapter)

                    if not chapter_found:
                        raise HTTPException(status_code=404, detail="找不到指定的章節")

                    # 更新 content
                    content["chapters"] = new_chapters
                    current_time = datetime.now()

                    # 刪除相關的 blocks
                    if block_ids_to_delete:
                        block_ids_placeholder = ','.join(['%s'] * len(block_ids_to_delete))
                        await cur.execute(f"""
                            DELETE FROM ReportContentBlocks 
                            WHERE BlockID IN ({block_ids_placeholder})
                        """, tuple(block_ids_to_delete))

                    # 刪除相關的權限映射
                    if permission_ids_to_delete:
                        permission_ids_placeholder = ','.join(['%s'] * len(permission_ids_to_delete))
                        await cur.execute(f"""
                            DELETE FROM RolePermissionMappings 
                            WHERE PermissionChapterID IN ({permission_ids_placeholder})
                        """, tuple(permission_ids_to_delete))

                    # 更新資產內容
                    await cur.execute("""
                        UPDATE OrganizationAssets 
                        SET Content = %s, UpdatedAt = %s
                        WHERE AssetID = %s
                    """, (json.dumps(content), current_time, asset_id_binary))

                    await conn.commit()

                    return {
                        "status": "success",
                        "message": "章節刪除成功",
                        "data": {
                            "asset_id": asset_id,
                            "deleted_chapter": chapter_title,
                            "updated_at": current_time.isoformat()
                        }
                    }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 新增報告書中章節
@app.post("/api/report/add_subchapter")
async def add_subchapter(data: dict):
    try:
        # 獲取輸入參數
        asset_id = data.get("asset_id")
        chapter_title = data.get("chapter_title")
        subchapter_title = data.get("subchapter_title")
        user_id = data.get("user_id")

        # 參數驗證
        if not all([asset_id, chapter_title, subchapter_title, user_id]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 生成新的UUID
        block_id = str(uuid.uuid4()).replace("-", "")
        access_permissions = str(uuid.uuid4()).replace("-", "")
        current_time = datetime.now()

        # 獲取資料庫連接
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 將字符串ID轉換為二進制格式
                asset_id_binary = bytes.fromhex(asset_id)
                user_id_binary = bytes.fromhex(user_id)

                # 獲取資產內容
                await cur.execute(
                    "SELECT Content, OrganizationID FROM OrganizationAssets WHERE AssetID = %s",
                    (asset_id_binary,)
                )
                result = await cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="找不到指定的資產")
                
                content = json.loads(result[0])
                organization_id_binary = result[1]

                # 在content中找到對應的chapter並添加新的subchapter
                chapter_found = False
                for chapter in content["chapters"]:
                    if chapter["chapterTitle"] == chapter_title:
                        chapter_found = True
                        # 檢查是否已存在相同的subchapter_title
                        for subchapter in chapter["subChapters"]:
                            if subchapter["subChapterTitle"] == subchapter_title:
                                raise HTTPException(status_code=400, detail="子章節標題已存在")
                        
                        # 添加新的subchapter
                        chapter["subChapters"].append({
                            "subChapterTitle": subchapter_title,
                            "BlockID": block_id,
                            "access_permissions": access_permissions,
                            "text_content":"",
                            "img_content_url": []

                        })
                        break

                if not chapter_found:
                    raise HTTPException(status_code=404, detail="找不到指定的章節")

                # 更新OrganizationAssets的content
                await cur.execute(
                    "UPDATE OrganizationAssets SET Content = %s, UpdatedAt = %s WHERE AssetID = %s",
                    (json.dumps(content), current_time, asset_id_binary)
                )

                # 創建新的ReportContentBlocks記錄
                block_id_binary = bytes.fromhex(block_id)
                await cur.execute(
                    """INSERT INTO ReportContentBlocks 
                       (BlockID, AssetID, status, content, ModifiedBy)
                       VALUES (%s, %s, 'editing', %s, %s)""",
                    (block_id_binary, asset_id_binary, 
                     json.dumps({"BlockID": f"{block_id}", "subChapterTitle": f"{subchapter_title}", "content": {"text": "", "images": [], "guidelines": {}, "comments": []}}),
                     user_id_binary)
                )

                # 獲取組織的所有角色
                await cur.execute(
                    "SELECT RoleID FROM Roles WHERE OrganizationID = %s",
                    (organization_id_binary,)
                )
                roles = await cur.fetchall()

                # 創建RolePermissionMappings記錄
                permission_chapter_id_binary = bytes.fromhex(access_permissions)
                for role in roles:
                    await cur.execute(
                        """INSERT INTO RolePermissionMappings 
                           (RoleID, PermissionChapterID, AssetID, ResourceType, ActionType)
                           VALUES (%s, %s, %s, 'report', 'read')""",
                        (role[0], permission_chapter_id_binary, asset_id_binary)
                    )

                await conn.commit()

                return {
                    "status": "success",
                    "message": "子章節添加成功",
                    "data": {
                        "asset_id": asset_id,
                        "chapter_title": chapter_title,
                        "subchapter_title": subchapter_title,
                        "block_id": block_id,
                        "access_permissions": access_permissions,
                        "updated_at": current_time.isoformat()
                    }
                }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 更改報告書中章節名稱(rename)
@app.post("/api/report/rename_subchapter")
async def rename_subchapter(data: dict):
    try:
        # 獲取必要參數
        asset_id = data.get("AssetID")
        chapter_title = data.get("chapterTitle")
        subchapter_title = data.get("subChapterTitle")
        new_subchapter_title = data.get("new_subChapterTitle")

        # 驗證必要參數
        if not all([asset_id, chapter_title, subchapter_title, new_subchapter_title]):
            raise HTTPException(status_code=400, detail="缺少必要參數")
        
        # 獲取資料庫連接
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始交易
                    await conn.begin()
                    
                    # 將 asset_id 轉換為 bytes
                    asset_id_binary = bytes.fromhex(asset_id.replace('-', ''))

                    # 檢查是否已存在相同名稱的子章節
                    await cur.execute("""
                        SELECT Content 
                        FROM OrganizationAssets 
                        WHERE AssetID = %s AND IsDeleted = FALSE
                        FOR UPDATE
                    """, (asset_id_binary,))
                    
                    result = await cur.fetchone()
                    if not result:
                        raise HTTPException(status_code=404, detail="找不到指定的資產")

                    content = json.loads(result[0]) if result[0] else {}
                    
                    # 在內容中找到並更新子章節名稱
                    found = False
                    name_exists = False
                    if "chapters" in content:
                        for chapter in content["chapters"]:
                            if chapter.get("chapterTitle") == chapter_title:
                                # 檢查新名稱是否已存在
                                for subchapter in chapter["subChapters"]:
                                    if subchapter.get("subChapterTitle") == new_subchapter_title:
                                        name_exists = True
                                        break
                                    elif subchapter.get("subChapterTitle") == subchapter_title:
                                        found = True
                                        subchapter["subChapterTitle"] = new_subchapter_title
                                if name_exists:
                                    raise HTTPException(status_code=400, detail="新的子章節名稱已存在")
                                break

                    if not found:
                        raise HTTPException(status_code=404, detail="找不到指定的章節或子章節")

                    # 更新資產內容和更新時間
                    current_time = datetime.now()
                    await cur.execute("""
                        UPDATE OrganizationAssets 
                        SET Content = %s, UpdatedAt = %s
                        WHERE AssetID = %s
                    """, (json.dumps(content), current_time, asset_id_binary))

                    # 提交交易
                    await conn.commit()

                    print(f"更新成功: asset_id={asset_id}, content={json.dumps(content)}")  # 添加調試日誌

                    return {
                        "status": "success",
                        "message": "子章節名稱更新成功",
                        "data": {
                            "asset_id": asset_id,
                            "chapter_title": chapter_title,
                            "old_subchapter_title": subchapter_title,
                            "new_subchapter_title": new_subchapter_title,
                            "updated_at": current_time.isoformat()
                        }
                    }
                except Exception as e:
                    # 發生錯誤時回滾交易
                    await conn.rollback()
                    raise e

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"錯誤詳情: {str(e)}")  # 添加錯誤日誌
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 刪除報告書中章節
@app.post("/api/report/delete_subchapter")
async def delete_subchapter(data: dict):
    try:
        # 獲取必要參數
        asset_id = data.get("AssetID")
        chapter_title = data.get("chapterTitle")
        subchapter_title = data.get("subChapterTitle")

        if not all([asset_id, chapter_title, subchapter_title]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 獲取資料庫連接
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 將 asset_id 轉換為 bytes
                asset_id_binary = bytes.fromhex(asset_id.replace('-', ''))

                # 獲取 organizationassets 的 content
                await cur.execute(
                    "SELECT Content FROM OrganizationAssets WHERE AssetID = %s AND IsDeleted = FALSE",
                    (asset_id_binary,)
                )
                result = await cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="找不到指定的資產")

                content = json.loads(result[0])
                block_id = None
                access_permissions = None
                content_updated = False

                # 遍歷章節找到要刪除的子章節
                for chapter in content.get("chapters", []):
                    if chapter["chapterTitle"] == chapter_title:
                        for i, subchapter in enumerate(chapter.get("subChapters", [])):
                            if subchapter["subChapterTitle"] == subchapter_title:
                                block_id = subchapter.get("BlockID")
                                access_permissions = subchapter.get("access_permissions")
                                # 刪除子章節
                                chapter["subChapters"].pop(i)
                                content_updated = True
                                break
                        break

                if not content_updated:
                    raise HTTPException(status_code=404, detail="找不到指定的子章節")

                # 更新 content
                await cur.execute(
                    "UPDATE OrganizationAssets SET Content = %s, UpdatedAt = CURRENT_TIMESTAMP WHERE AssetID = %s",
                    (json.dumps(content), asset_id_binary)
                )

                # 如果有 BlockID，刪除相關的 reportcontentblocks 記錄
                if block_id:
                    block_id_binary = bytes.fromhex(block_id.replace('-', ''))
                    await cur.execute(
                        "DELETE FROM ReportContentBlocks WHERE BlockID = %s",
                        (block_id_binary,)
                    )

                # 如果有 access_permissions，刪除相關的 rolepermissionmappings 記錄
                if access_permissions:
                    permission_id_binary = bytes.fromhex(access_permissions.replace('-', ''))
                    await cur.execute(
                        "DELETE FROM RolePermissionMappings WHERE PermissionChapterID = %s",
                        (permission_id_binary,)
                    )

                await conn.commit()

                return {"status": "success", "message": "子章節已成功刪除"}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"錯誤詳情: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 新增_公司基本資料章節
@app.post("/api/report/add_company_info_chapter")
async def add_company_info_chapter(data: dict):
    try:
        # 獲取輸入參數
        asset_id = data.get("asset_id")
        chapter_title = data.get("chapter_title")
        subchapter_title = data.get("subchapter_title")
        chapter_level = data.get("chapter_level")
        user_id = data.get("user_id")

        # 驗證必要參數
        if not all([asset_id, chapter_title, subchapter_title, chapter_level, user_id]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        if chapter_level not in [1, 2, 3]:
            raise HTTPException(status_code=400, detail="章節等級必須是 1, 2, 或 3")

        # 獲取資料庫連接
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 將 asset_id 轉換為 bytes
                asset_id_binary = bytes.fromhex(asset_id.replace('-', ''))

                # 獲取資產內容
                await cur.execute(
                    "SELECT Content FROM OrganizationAssets WHERE AssetID = %s",
                    (asset_id_binary,)
                )
                result = await cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="找不到指定的資產")

                content = json.loads(result[0])

                # 根據不同章節等級處理
                if chapter_level == 1:
                    # 新增最上層章節
                    new_chapter = {
                        "chapterTitle": chapter_title,
                        "subChapters": []
                    }
                    content["chapters"].append(new_chapter)

                    # 同步更修報告書的章節，因為是對應關係。
                    # 先判斷 報告書和公司資料是否有對應關係
                    # 去 reportcompanyinfomapping 查詢 報告書的 report_asset_id
                    # 獲取資產內容
                    await cur.execute(
                        "SELECT ReportID FROM ReportCompanyInfoMapping WHERE CompanyInfoID = %s",
                        (asset_id_binary,)
                    )
                    report_asset_result = await cur.fetchone()

                    # 判斷 report_asset_id 是否有值 是否為空 如果為空 代表沒有對應關係 不用同步更修報告書的章節
                    if report_asset_result and report_asset_result[0]:  # 檢查是否為 None 以及第一個元素 (ReportID) 是否存在且不為空
                        # report_asset_id 存在，表示有對應關係，進行同步更修報告書章節的邏輯
                        report_asset_id = report_asset_result[0]  # 取得 ReportID
                        # 將二進制的 UUID 轉換為字符串格式
                        report_asset_id_str = str(uuid.UUID(bytes=report_asset_id))
                        # 使用 await 調用異步函數
                        await update_report_outline_add_chapter_title({
                            "asset_id": report_asset_id_str,
                            "chapterTitle": chapter_title
                        })
                    else:
                        # 如果為空 代表沒有對應關係 不用同步更修報告書的章節
                        print("沒有找到對應的報告書，不進行章節同步。")
                        pass

                elif chapter_level == 2:
                    # 在指定的上層章節下新增次層章節
                    chapter_found = False
                    for chapter in content["chapters"]:
                        if chapter["chapterTitle"] == chapter_title:
                            new_subchapter = {
                                "subChapterTitle": subchapter_title,
                                "subSubChapters": []
                            }
                            chapter["subChapters"].append(new_subchapter)
                            chapter_found = True
                            break

                    if not chapter_found:
                        raise HTTPException(status_code=404, detail="找不到指定的上層章節")
                    
                    # 同步更修報告書的章節，因為是對應關係。
                    # 先判斷 報告書和公司資料是否有對應關係
                    # 去 reportcompanyinfomapping 查詢 報告書的 report_asset_id
                    # 獲取資產內容
                    await cur.execute(
                        "SELECT ReportID FROM ReportCompanyInfoMapping WHERE CompanyInfoID = %s",
                        (asset_id_binary,)
                    )
                    report_asset_result = await cur.fetchone()

                    # 判斷 report_asset_id 是否有值 是否為空 如果為空 代表沒有對應關係 不用同步更修報告書的章節
                    if report_asset_result and report_asset_result[0]:  # 檢查是否為 None 以及第一個元素 (ReportID) 是否存在且不為空
                        # report_asset_id 存在，表示有對應關係，進行同步更修報告書章節的邏輯
                        report_asset_id = report_asset_result[0]  # 取得 ReportID
                        # 將二進制的 UUID 轉換為字符串格式
                        report_asset_id_str = str(uuid.UUID(bytes=report_asset_id))
                        # 使用 await 調用異步函數
                        print("user_id", user_id) # 輸出：4ab19295b506448db952c910a51c00e5
                        print("report_asset_id_str", report_asset_id_str)
                        await add_subchapter({
                            "asset_id": report_asset_id_str.replace("-", ""),
                            "chapter_title": chapter_title,
                            "subchapter_title": subchapter_title,
                            "user_id": user_id
                        })
                    else:
                        # 如果為空 代表沒有對應關係 不用同步更修報告書的章節
                        print("沒有找到對應的報告書，不進行章節同步。")
                        pass

                elif chapter_level == 3:
                    # 在指定的次層章節下新增最下層章節
                    chapter_found = False
                    subchapter_found = False

                    for chapter in content["chapters"]:
                        for subchapter in chapter["subChapters"]:
                            if subchapter["subChapterTitle"] == chapter_title:
                                # 生成新的 UUID
                                block_id = str(uuid.uuid4())
                                access_permissions = str(uuid.uuid4())

                                new_subsubchapter = {
                                    "subSubChapterTitle": subchapter_title,
                                    "BlockID": block_id,
                                    "access_permissions": access_permissions
                                }
                                subchapter["subSubChapters"].append(new_subsubchapter)

                                # 新增 reportcontentblocks 記錄
                                block_content = {
                                    "BlockID": block_id,
                                    "subChapterTitle": subchapter_title,
                                    "content": {
                                        "text": "",
                                        "images": [],
                                        "guidelines": {},
                                        "comments": []
                                    }
                                }

                                await cur.execute(
                                    """
                                    INSERT INTO ReportContentBlocks 
                                    (BlockID, AssetID, content) 
                                    VALUES (%s, %s, %s)
                                    """,
                                    (
                                        bytes.fromhex(block_id.replace('-', '')),
                                        asset_id_binary,
                                        json.dumps(block_content)
                                    )
                                )

                                # 獲取組織的 RoleName="一般"
                                await cur.execute(
                                    """
                                    SELECT RoleID FROM Roles 
                                    WHERE OrganizationID = (
                                        SELECT OrganizationID 
                                        FROM OrganizationAssets 
                                        WHERE AssetID = %s
                                    )
                                    AND RoleName = %s
                                    """,
                                    (asset_id_binary, "一般")
                                )
                                roles = await cur.fetchall()

                                # 為每個角色新增權限映射 實際上是一般後續可以修改
                                for role in roles:
                                    await cur.execute(
                                        """
                                        INSERT INTO RolePermissionMappings 
                                        (RoleID, PermissionChapterID, AssetID, ResourceType, ActionType) 
                                        VALUES (%s, %s, %s, %s, %s)
                                        """,
                                        (
                                            role[0],
                                            bytes.fromhex(access_permissions.replace('-', '')),
                                            asset_id_binary,
                                            'company_info',
                                            'read_write'
                                        )
                                    )

                                subchapter_found = True
                                break
                        if subchapter_found:
                            break

                    if not subchapter_found:
                        raise HTTPException(status_code=404, detail="找不到指定的次層章節")

                # 更新資產內容
                await cur.execute(
                    "UPDATE OrganizationAssets SET Content = %s WHERE AssetID = %s",
                    (json.dumps(content), asset_id_binary)
                )

                await conn.commit()

                return {"status": "success", "message": "章節新增成功"}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"錯誤詳情: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 刪除_公司基本資料章節
@app.post("/api/report/delete_company_info_chapter")
async def delete_company_info_chapter(data: dict):
    try:
        # 獲取輸入參數
        asset_id = data.get("asset_id")
        chapter_title = data.get("chapter_title")
        subchapter_title = data.get("subchapter_title")
        chapter_level = data.get("chapter_level")

        # 驗證必要參數
        if not all([asset_id, chapter_title, subchapter_title, chapter_level]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        if chapter_level not in [1, 2, 3]:
            raise HTTPException(status_code=400, detail="章節等級必須是 1, 2, 或 3")

        # 獲取資料庫連接
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 將 asset_id 轉換為 bytes
                asset_id_binary = bytes.fromhex(asset_id.replace('-', ''))

                # 獲取資產內容
                await cur.execute(
                    "SELECT Content FROM OrganizationAssets WHERE AssetID = %s",
                    (asset_id_binary,)
                )
                result = await cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="找不到指定的資產")

                content = json.loads(result[0])

                # 根據不同章節等級處理
                if chapter_level == 1:
                    # 刪除最上層章節
                    chapter_found = False
                    for i, chapter in enumerate(content["chapters"]):
                        if chapter["chapterTitle"] == chapter_title:
                            # 檢查是否有子章節包含 BlockID，如果有需要刪除相關資料
                            for subchapter in chapter["subChapters"]:
                                for subsubchapter in subchapter.get("subSubChapters", []):
                                    if "BlockID" in subsubchapter and "access_permissions" in subsubchapter:
                                        block_id = subsubchapter["BlockID"]
                                        access_permissions = subsubchapter["access_permissions"]
                                        
                                        # 刪除 reportcontentblocks 記錄
                                        await cur.execute(
                                            "DELETE FROM ReportContentBlocks WHERE BlockID = %s",
                                            (bytes.fromhex(block_id.replace('-', '')),)
                                        )
                                        
                                        # 刪除權限映射
                                        await cur.execute(
                                            "DELETE FROM RolePermissionMappings WHERE PermissionChapterID = %s",
                                            (bytes.fromhex(access_permissions.replace('-', '')),)
                                        )
                            
                            del content["chapters"][i]
                            chapter_found = True
                            break

                    if not chapter_found:
                        raise HTTPException(status_code=404, detail="找不到指定的章節")
                    
                    # 同步更修報告書的章節，因為是對應關係。
                    # 先判斷 報告書和公司資料是否有對應關係
                    # 去 reportcompanyinfomapping 查詢 報告書的 report_asset_id
                    # 獲取資產內容
                    await cur.execute(
                        "SELECT ReportID FROM ReportCompanyInfoMapping WHERE CompanyInfoID = %s",
                        (asset_id_binary,)
                    )
                    report_asset_result = await cur.fetchone()

                    # 判斷 report_asset_id 是否有值 是否為空 如果為空 代表沒有對應關係 不用同步更修報告書的章節
                    if report_asset_result and report_asset_result[0]:  # 檢查是否為 None 以及第一個元素 (ReportID) 是否存在且不為空
                        # report_asset_id 存在，表示有對應關係，進行同步更修報告書章節的邏輯
                        report_asset_id = report_asset_result[0]  # 取得 ReportID
                        # 將二進制的 UUID 轉換為字符串格式
                        report_asset_id_str = str(uuid.UUID(bytes=report_asset_id))
                        # 使用 await 調用異步函數
                        await delete_report_outline({
                            "asset_id": report_asset_id_str,
                            "chapterTitle": chapter_title
                        })
                    else:
                        # 如果為空 代表沒有對應關係 不用同步更修報告書的章節
                        print("沒有找到對應的報告書，不進行章節同步。")
                        pass

                elif chapter_level == 2:
                    # 刪除次層章節
                    chapter_found = False
                    subchapter_found = False
                    for chapter in content["chapters"]:
                        if chapter["chapterTitle"] == chapter_title:
                            chapter_found = True
                            for i, subchapter in enumerate(chapter["subChapters"]):
                                if subchapter["subChapterTitle"] == subchapter_title:
                                    # 檢查是否有子章節包含 BlockID，如果有需要刪除相關資料
                                    for subsubchapter in subchapter.get("subSubChapters", []):
                                        if "BlockID" in subsubchapter and "access_permissions" in subsubchapter:
                                            block_id = subsubchapter["BlockID"]
                                            access_permissions = subsubchapter["access_permissions"]
                                            
                                            # 刪除 reportcontentblocks 記錄
                                            await cur.execute(
                                                "DELETE FROM ReportContentBlocks WHERE BlockID = %s",
                                                (bytes.fromhex(block_id.replace('-', '')),)
                                            )
                                            
                                            # 刪除權限映射
                                            await cur.execute(
                                                "DELETE FROM RolePermissionMappings WHERE PermissionChapterID = %s",
                                                (bytes.fromhex(access_permissions.replace('-', '')),)
                                            )
                                    
                                    del chapter["subChapters"][i]
                                    subchapter_found = True
                                    break
                            break

                    if not chapter_found:
                        raise HTTPException(status_code=404, detail="找不到指定的上層章節")
                    if not subchapter_found:
                        raise HTTPException(status_code=404, detail="找不到指定的次層章節")
                    
                    # 同步更修報告書的章節，因為是對應關係。
                    # 先判斷 報告書和公司資料是否有對應關係
                    # 去 reportcompanyinfomapping 查詢 報告書的 report_asset_id
                    # 獲取資產內容
                    await cur.execute(
                        "SELECT ReportID FROM ReportCompanyInfoMapping WHERE CompanyInfoID = %s",
                        (asset_id_binary,)
                    )
                    report_asset_result = await cur.fetchone()

                    # 判斷 report_asset_id 是否有值 是否為空 如果為空 代表沒有對應關係 不用同步更修報告書的章節
                    if report_asset_result and report_asset_result[0]:  # 檢查是否為 None 以及第一個元素 (ReportID) 是否存在且不為空
                        # report_asset_id 存在，表示有對應關係，進行同步更修報告書章節的邏輯
                        report_asset_id = report_asset_result[0]  # 取得 ReportID
                        # 將二進制的 UUID 轉換為字符串格式
                        report_asset_id_str = str(uuid.UUID(bytes=report_asset_id))
                        # 使用 await 調用異步函數
                        await delete_subchapter({
                            "AssetID": report_asset_id_str,
                            "chapterTitle": chapter_title,
                            "subChapterTitle": subchapter_title
                        })
                    else:
                        # 如果為空 代表沒有對應關係 不用同步更修報告書的章節
                        print("沒有找到對應的報告書，不進行章節同步。")
                        pass

                elif chapter_level == 3:
                    # 刪除最下層章節
                    subchapter_found = False
                    subsubchapter_found = False
                    for chapter in content["chapters"]:
                        for subchapter in chapter["subChapters"]:
                            if subchapter["subChapterTitle"] == chapter_title:
                                subchapter_found = True
                                for i, subsubchapter in enumerate(subchapter["subSubChapters"]):
                                    if subsubchapter["subSubChapterTitle"] == subchapter_title:
                                        # 獲取 BlockID 和 access_permissions
                                        block_id = subsubchapter["BlockID"]
                                        access_permissions = subsubchapter["access_permissions"]
                                        
                                        # 刪除 reportcontentblocks 記錄
                                        await cur.execute(
                                            "DELETE FROM ReportContentBlocks WHERE BlockID = %s",
                                            (bytes.fromhex(block_id.replace('-', '')),)
                                        )
                                        
                                        # 刪除權限映射
                                        await cur.execute(
                                            "DELETE FROM RolePermissionMappings WHERE PermissionChapterID = %s",
                                            (bytes.fromhex(access_permissions.replace('-', '')),)
                                        )
                                        
                                        del subchapter["subSubChapters"][i]
                                        subsubchapter_found = True
                                        break
                                break
                        if subchapter_found:
                            break

                    if not subchapter_found:
                        raise HTTPException(status_code=404, detail="找不到指定的次層章節")
                    if not subsubchapter_found:
                        raise HTTPException(status_code=404, detail="找不到指定的最下層章節")

                # 更新資產內容
                await cur.execute(
                    "UPDATE OrganizationAssets SET Content = %s WHERE AssetID = %s",
                    (json.dumps(content), asset_id_binary)
                )

                await conn.commit()

                return {"status": "success", "message": "章節刪除成功"}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"錯誤詳情: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 編輯_公司基本資料章節名稱
@app.post("/api/report/edit_company_info_chapter_title")
async def edit_company_info_chapter_title(data: dict):
    try:
        # 獲取輸入參數
        asset_id = data.get("asset_id")
        chapter_title = data.get("chapter_title")
        subchapter_title = data.get("subchapter_title")
        new_chapter_title = data.get("new_chapter_title")
        chapter_level = data.get("chapter_level")

        # 驗證必要參數
        if not all([asset_id, chapter_title, subchapter_title, new_chapter_title, chapter_level]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        if chapter_level not in [1, 2, 3]:
            raise HTTPException(status_code=400, detail="章節等級必須是 1, 2, 或 3")

        # 獲取資料庫連接
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 將 asset_id 轉換為 bytes
                asset_id_binary = bytes.fromhex(asset_id.replace('-', ''))

                # 獲取資產內容
                await cur.execute(
                    "SELECT Content FROM OrganizationAssets WHERE AssetID = %s",
                    (asset_id_binary,)
                )
                result = await cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="找不到指定的資產")

                content = json.loads(result[0])

                # 根據不同章節等級處理
                if chapter_level == 1:
                    # 編輯最上層章節名稱
                    chapter_found = False
                    for chapter in content["chapters"]:
                        if chapter["chapterTitle"] == chapter_title:
                            chapter["chapterTitle"] = new_chapter_title
                            chapter_found = True
                            break

                    if not chapter_found:
                        raise HTTPException(status_code=404, detail="找不到指定的章節")
                    
                    # 同步更修報告書的章節，因為是對應關係。
                    # 先判斷 報告書和公司資料是否有對應關係
                    # 去 reportcompanyinfomapping 查詢 報告書的 report_asset_id
                    # 獲取資產內容
                    await cur.execute(
                        "SELECT ReportID FROM ReportCompanyInfoMapping WHERE CompanyInfoID = %s",
                        (asset_id_binary,)
                    )
                    report_asset_result = await cur.fetchone()

                    # 判斷 report_asset_id 是否有值 是否為空 如果為空 代表沒有對應關係 不用同步更修報告書的章節
                    if report_asset_result and report_asset_result[0]:  # 檢查是否為 None 以及第一個元素 (ReportID) 是否存在且不為空
                        # report_asset_id 存在，表示有對應關係，進行同步更修報告書章節的邏輯
                        report_asset_id = report_asset_result[0]  # 取得 ReportID
                        # 將二進制的 UUID 轉換為字符串格式
                        report_asset_id_str = str(uuid.UUID(bytes=report_asset_id))
                        # 使用 await 調用異步函數
                        await rename_chapter_title({
                            "asset_id": report_asset_id_str,
                            "chapter_title": chapter_title,
                            "new_chapter_title": new_chapter_title
                        })
                    else:
                        # 如果為空 代表沒有對應關係 不用同步更修報告書的章節
                        print("沒有找到對應的報告書，不進行章節同步。")
                        pass

                    report_asset_id_bytes = uuid.UUID(report_asset_id_str).bytes

                    # 同步修正 "workflowstages" 表 "ChapterName"
                    # 先查詢 "workflowstages" 表 "AssetID" 是否等於 asset_id，and "ChapterName" 是否等於 chapter_title
                    await cur.execute(
                        "SELECT WorkflowStageID FROM WorkflowStages WHERE AssetID = %s AND ChapterName = %s",
                        (report_asset_id_bytes, chapter_title)
                    )
                    workflow_asset_result = await cur.fetchone() # 注意只會有一筆

                    # 如果有值 WorkflowStageID 就更新 ChapterName
                    if workflow_asset_result and workflow_asset_result[0]:
                        # 有可能會一次更新多筆，所以需要使用 WHERE 條件
                        await cur.execute(
                            "UPDATE WorkflowStages SET ChapterName = %s WHERE AssetID = %s AND ChapterName = %s",
                            (new_chapter_title, report_asset_id_bytes, chapter_title)
                        )
                        await conn.commit()

                    # 同步修正 "workflowinstances" 表 "ChapterName"
                    # 先查詢 "workflowinstances" 表 "AssetID" 是否等於 report_asset_id_bytes 和 "ChapterName" 是否等於 chapter_title
                    await cur.execute(
                        "SELECT WorkflowInstanceID FROM WorkflowInstances WHERE AssetID = %s AND ChapterName = %s",
                        (report_asset_id_bytes, chapter_title)
                    )
                    workflow_instance_result = await cur.fetchone()

                    # 如果有值 WorkflowInstanceID 就更新 ChapterName
                    if workflow_instance_result and workflow_instance_result[0]:
                        await cur.execute(
                            "UPDATE WorkflowInstances SET ChapterName = %s WHERE AssetID = %s AND ChapterName = %s",
                            (new_chapter_title, report_asset_id_bytes, chapter_title)
                        )
                        await conn.commit()

                elif chapter_level == 2:
                    # 編輯次層章節名稱
                    chapter_found = False
                    subchapter_found = False
                    for chapter in content["chapters"]:
                        if chapter["chapterTitle"] == chapter_title:
                            chapter_found = True
                            for subchapter in chapter["subChapters"]:
                                if subchapter["subChapterTitle"] == subchapter_title:
                                    subchapter["subChapterTitle"] = new_chapter_title
                                    subchapter_found = True
                                    break
                            break

                    if not chapter_found:
                        raise HTTPException(status_code=404, detail="找不到指定的上層章節")
                    if not subchapter_found:
                        raise HTTPException(status_code=404, detail="找不到指定的次層章節")
                    
                    # 同步更修報告書的章節，因為是對應關係。
                    # 先判斷 報告書和公司資料是否有對應關係
                    # 去 reportcompanyinfomapping 查詢 報告書的 report_asset_id
                    # 獲取資產內容
                    await cur.execute(
                        "SELECT ReportID FROM ReportCompanyInfoMapping WHERE CompanyInfoID = %s",
                        (asset_id_binary,)
                    )
                    report_asset_result = await cur.fetchone()

                    # 判斷 report_asset_id 是否有值 是否為空 如果為空 代表沒有對應關係 不用同步更修報告書的章節
                    if report_asset_result and report_asset_result[0]:  # 檢查是否為 None 以及第一個元素 (ReportID) 是否存在且不為空
                        # report_asset_id 存在，表示有對應關係，進行同步更修報告書章節的邏輯
                        report_asset_id = report_asset_result[0]  # 取得 ReportID
                        # 將二進制的 UUID 轉換為字符串格式
                        report_asset_id_str = str(uuid.UUID(bytes=report_asset_id))
                        # 使用 await 調用異步函數
                        await rename_subchapter({
                            "AssetID": report_asset_id_str,
                            "chapterTitle": chapter_title,
                            "subChapterTitle": subchapter_title,
                            "new_subChapterTitle": new_chapter_title
                        })
                    else:
                        # 如果為空 代表沒有對應關係 不用同步更修報告書的章節
                        print("沒有找到對應的報告書，不進行章節同步。")
                        pass

                elif chapter_level == 3:
                    # 編輯最下層章節名稱
                    subchapter_found = False
                    subsubchapter_found = False
                    block_id = None
                    for chapter in content["chapters"]:
                        for subchapter in chapter["subChapters"]:
                            if subchapter["subChapterTitle"] == chapter_title:
                                subchapter_found = True
                                for subsubchapter in subchapter["subSubChapters"]:
                                    if subsubchapter["subSubChapterTitle"] == subchapter_title:
                                        subsubchapter["subSubChapterTitle"] = new_chapter_title
                                        block_id = subsubchapter["BlockID"]
                                        subsubchapter_found = True
                                        break
                                break
                        if subchapter_found and subsubchapter_found:
                            break

                    if not subchapter_found:
                        raise HTTPException(status_code=404, detail="找不到指定的次層章節")
                    if not subsubchapter_found:
                        raise HTTPException(status_code=404, detail="找不到指定的最下層章節")

                    # 更新 reportcontentblocks 的內容
                    if block_id:
                        await cur.execute(
                            "SELECT content FROM ReportContentBlocks WHERE BlockID = %s",
                            (bytes.fromhex(block_id.replace('-', '')),)
                        )
                        block_result = await cur.fetchone()
                        if block_result:
                            block_content = json.loads(block_result[0])
                            block_content["subChapterTitle"] = new_chapter_title
                            
                            await cur.execute(
                                "UPDATE ReportContentBlocks SET content = %s WHERE BlockID = %s",
                                (json.dumps(block_content), bytes.fromhex(block_id.replace('-', '')))
                            )

                # 更新資產內容
                await cur.execute(
                    "UPDATE OrganizationAssets SET Content = %s WHERE AssetID = %s",
                    (json.dumps(content), asset_id_binary)
                )

                await conn.commit()

                return {"status": "success", "message": "章節名稱修改成功"}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"錯誤詳情: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 生成報告書文字
@app.post("/api/report/generate_text")
async def generate_text(data: dict):
    try:
        # 獲取必要參數
        company_info_assetID = data.get("company_info_assetID")
        chapter_title = data.get("chapter_title")
        sub_chapter_title = data.get("sub_chapter_title")

        if not all([company_info_assetID, chapter_title, sub_chapter_title]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 獲取資料庫連接
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 將 company_info_assetID 轉換為 bytes
                asset_id_binary = bytes.fromhex(company_info_assetID.replace('-', ''))

                # 從 organizationassets 獲取資產內容
                await cur.execute(
                    "SELECT Content, Category FROM OrganizationAssets WHERE AssetID = %s AND IsDeleted = FALSE",
                    (asset_id_binary,)
                )
                result = await cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="找不到指定的資產")

                assets_content = json.loads(result[0])
                category = result[1]
                # 尋找對應的章節和子章節
                target_sub_sub_chapters = None
                for chapter in assets_content.get("chapters", []):
                    if chapter["chapterTitle"] == chapter_title:
                        for sub_chapter in chapter.get("subChapters", []):
                            if sub_chapter["subChapterTitle"] == sub_chapter_title:
                                target_sub_sub_chapters = sub_chapter.get("subSubChapters", [])
                                break
                        break

                if not target_sub_sub_chapters:
                    raise HTTPException(status_code=404, detail="找不到指定的章節或子章節")

                # 生成輸出文字
                output_text = ""
                for sub_sub_chapter in target_sub_sub_chapters:
                    block_id = sub_sub_chapter["BlockID"]
                    block_id_binary = bytes.fromhex(block_id.replace('-', ''))

                    # 從 reportcontentblocks 獲取區塊內容
                    await cur.execute(
                        "SELECT content FROM ReportContentBlocks WHERE BlockID = %s",
                        (block_id_binary,)
                    )
                    block_result = await cur.fetchone()
                    if block_result:
                        block_content = json.loads(block_result[0])
                        text_content = block_content.get("content", {}).get("text", "")
                        output_text += f"{sub_sub_chapter['subSubChapterTitle']}:{text_content}\n\n"
                output_text = output_text.strip()

                
                # 建立物件
                generator = GeminiGenerator(api_keys, model_name, config, base_url, max_retry)
                # 獲取訓練數據
                url = "http://localhost:8001/api/Sample_Report.json"
                messages = generator.get_messages(category, chapter_title, sub_chapter_title, url)

                prompt = output_text
                # print(messages)
                response = await generator.generate_text(messages, prompt)

                return {"status": "success", "text": response.content.replace("*   ", "").replace("*", "")}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"錯誤詳情: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 更新檢驗結果
@app.post("/api/report/update_verification_result")
async def update_verification_result(data: dict):
    try:
        # 獲取必要參數
        asset_id = data.get("AssetID")
        chapter_title = data.get("chapterTitle")
        guidelines = data.get("guidelines")

        print(f"接收到的參數: asset_id={asset_id}, chapter_title={chapter_title}")

        # 驗證必要參數
        if not all([asset_id, chapter_title, guidelines]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 獲取資料庫連接
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()
                    
                    # 將 asset_id 轉換為二進制格式
                    asset_id_binary = bytes.fromhex(asset_id.replace('-', ''))

                    # 獲取資產內容
                    await cur.execute(
                        """
                        SELECT Content 
                        FROM OrganizationAssets 
                        WHERE AssetID = %s AND IsDeleted = FALSE
                        """,
                        (asset_id_binary,)
                    )
                    result = await cur.fetchone()

                    if not result:
                        raise HTTPException(status_code=404, detail="未找到指定資產")

                    print(f"當前資產內容: {result[0]}")

                    # 解析當前內容
                    content = json.loads(result[0])
                    
                    # 更新指定章節的 guidelines
                    updated = False
                    for chapter in content["chapters"]:
                        if chapter["chapterTitle"] == chapter_title:
                            chapter["guidelines"] = guidelines
                            updated = True
                            break

                    if not updated:
                        raise HTTPException(status_code=404, detail="未找到指定章節")

                    # 更新資料庫
                    new_content = json.dumps(content)
                    print(f"更新後的內容: {new_content}")
                    
                    await cur.execute(
                        """
                        UPDATE OrganizationAssets 
                        SET Content = %s, UpdatedAt = CURRENT_TIMESTAMP 
                        WHERE AssetID = %s
                        """,
                        (new_content, asset_id_binary)
                    )

                    # 提交事務
                    await conn.commit()
                    print("資料庫更新成功")

                    return {"status": "success", "message": "檢驗結果已更新"}
                    
                except Exception as e:
                    # 如果發生錯誤，回滾事務
                    await conn.rollback()
                    print(f"資料庫更新失敗，已回滾: {str(e)}")
                    raise

    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"無效的UUID格式: {str(e)}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON解析錯誤: {str(e)}")
    except Exception as e:
        print(f"錯誤詳情: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 根據文字生成圖片(Mermaid)
@app.post("/api/report/generate_mermaid_image")
async def generate_mermaid_image(data: dict):
    try:
        # 檢查輸入參數
        if not data or "text" not in data:
            raise HTTPException(status_code=400, detail="缺少必要的文本參數")
            
        # 傳入文字
        text = data.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="文本內容不能為空")

        # 生成圖片
        try:
            gemini = GeminiGenerator(api_keys, model_name, config, base_url, max_retry)
            reference_data = await gemini.llm_to_mermaid(text)
            choice = reference_data.choices[0]
            message = choice.message
            content = message.content
            
            # 清理 Mermaid 語法
            content = content.replace("```mermaid", "").replace("```", "")
            content = content.replace("(", "").replace(")", "")
            
            # 生成圖片唯一碼
            unique_id = str(uuid.uuid4())
            output_filename = f"./images/{unique_id}.png"
            
            # 確保輸出目錄存在
            os.makedirs("./images", exist_ok=True)
            
            # 生成圖片
            try:
                mermaid_to_image(content, output_filename, format="png")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"生成圖片失敗: {str(e)}")

            # 構建圖片URL
            image_url = f"http://localhost:8000/images/{unique_id}.png"
            image_url = f"http://localhost:8001/images/9d5ced66-2019-4ad2-8d39-5f659ac13223.png"
            
            return {
                "status": "success",
                "message": "圖片已生成",
                "data": {
                    "image_url": image_url,
                    "mermaid_code": content
                }
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"生成 Mermaid 圖表失敗: {str(e)}")
            
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 獲取報告書資訊
@app.post("/api/report/get_report_info")
async def get_report_info(data: dict):
    try:
        # 獲取組織ID
        organization_id = data.get("organizationID")
        if not organization_id:
            return {"status": "error", "message": "缺少組織ID"}
        
        organization_id_binary = bytes.fromhex(organization_id.replace('-', ''))

        # 獲取資料庫連接
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # 獲取報告書資訊
                query = """
                    SELECT 
                        AssetID as assetID,
                        AssetName as assetName,
                        CreatedAt as createdAt,
                        UpdatedAt as updatedAt,
                        Status as status
                    FROM OrganizationAssets 
                    WHERE OrganizationID = %s
                    AND AssetType = 'report'
                    AND IsDeleted = FALSE
                    ORDER BY UpdatedAt DESC
                """
                await cur.execute(query, (organization_id_binary,))
                reports = await cur.fetchall()

                # 轉換report的assetID格式為字符串
                for report in reports:
                    report['assetID'] = uuid.UUID(bytes=report['assetID']).hex

                # 轉換日期時間格式為字符串
                for report in reports:
                    report['createdAt'] = report['createdAt'].isoformat() if report['createdAt'] else None
                    report['updatedAt'] = report['updatedAt'].isoformat() if report['updatedAt'] else None

                return {
                    "status": "success",
                    "data": reports
                }

    except Exception as e:
        print(f"Error in get_report_info: {str(e)}")
        return {
            "status": "error",
            "message": "獲取報告書資訊失敗"
        }


# 獲取報告書章節列表
@app.post("/api/report/get_report_chapters")
async def get_report_chapters(data: dict):
    # 傳入 AssetID
    asset_id = data.get("AssetID")
    if not asset_id:
        return {"status": "error", "message": "缺少資產ID"}
    
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 將字符串格式的UUID轉換為二進制
                asset_id_binary = uuid.UUID(asset_id).bytes

                # 查詢資產內容
                query = """
                    SELECT Content 
                    FROM OrganizationAssets 
                    WHERE AssetID = %s AND IsDeleted = FALSE
                """
                await cur.execute(query, (asset_id_binary,))
                result = await cur.fetchone()

                if not result:
                    return {
                        "status": "error",
                        "message": "找不到指定的資產"
                    }

                content = json.loads(result[0]) if result[0] else {}
                chapters = content.get("chapters", [])

                # 提取所有章節標題
                chapter_titles = []
                for chapter in chapters:
                    chapter_titles.append(chapter.get("chapterTitle", ""))

                return {
                    "status": "success",
                    "data": chapter_titles
                }

    except Exception as e:
        print(f"Error in get_report_chapters: {str(e)}")
        return {
            "status": "error",
            "message": "獲取報告書章節列表失敗"
        }


# 獲取組織可用的身分組
@app.post("/api/organization/approver-groups")
async def get_approver_groups(data: dict):
    try:
        # 獲取組織ID
        organization_id = data.get("organizationID")
        if not organization_id:
            return {"status": "error", "message": "缺少組織ID"}

        # 將傳入的 organization_id 轉換為 UUID 格式的 bytes
        org_id_bytes = uuid.UUID(organization_id).bytes

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 查詢該組織下的所有角色
                query = """
                    SELECT
                        RoleID as roleId,
                        RoleName as roleName,
                        Description as description,
                        Color as color,
                        CreatedAt as createdAt
                    FROM Roles
                    WHERE OrganizationID = %s
                """
                await cur.execute(query, (org_id_bytes,))
                roles_tuple_list = await cur.fetchall() # 取得的是 tuple 列表

                roles = [] # 創建一個新的列表來存放字典格式的角色資訊
                for role_tuple in roles_tuple_list:
                    role_dict = {
                        "roleId": uuid.UUID(bytes=role_tuple[0]).hex, # 使用數字索引 0 取 RoleID
                        "roleName": role_tuple[1], # 使用數字索引 1 取 RoleName
                        "description": role_tuple[2], # 使用數字索引 2 取 Description
                        "color": role_tuple[3], # 使用數字索引 3 取 Color
                        "createdAt": role_tuple[4].isoformat() if role_tuple[4] else None # 使用數字索引 4 取 CreatedAt
                    }
                    roles.append(role_dict)


                return {"status": "success", "data": roles}

    except ValueError as e:
        return {"status": "error", "message": "無效的組織ID格式"}
    except Exception as e:
        return {"status": "error", "message": f"獲取角色資訊失敗: {str(e)}"}


# 儲存審核流程階段
@app.post("/api/report/save_workflow_stage")
async def save_workflow_stage(data: dict):
    try:
        # 獲取輸入數據
        asset_id = data.get("assetID")
        chapter_name = data.get("chapterName")
        stage_settings = data.get("stageSettings")

        # 驗證必要參數
        if not all([asset_id, chapter_name]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的UUID轉換為二進制
        asset_id_binary = uuid.UUID(asset_id).bytes

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 使用 AssetID 和 ChapterName 查詢 workflowinstances 表，看是否已經存在實例並且 Status 為 審核中。
                await cur.execute("SELECT Status FROM WorkflowInstances WHERE AssetID = %s AND ChapterName = %s", (asset_id_binary, chapter_name))
                result = await cur.fetchone()
                if result and result[0] == '審核中':
                    return {"status": "error", "message": "審核中無法修改審核流程"}

                # 獲取組織ID
                await cur.execute(
                    "SELECT OrganizationID FROM OrganizationAssets WHERE AssetID = %s",
                    (asset_id_binary,)
                )
                result = await cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="找不到對應的資產")
                organization_id = result[0]

                # 先獲取現有的工作流程階段的 PermissionChapterID
                await cur.execute(
                    "SELECT PermissionChapterID FROM WorkflowStages WHERE AssetID = %s AND ChapterName = %s",
                    (asset_id_binary, chapter_name)
                )
                existing_permission_chapters = await cur.fetchall()
                
                # 刪除現有的工作流程階段
                await cur.execute(
                    "DELETE FROM WorkflowStages WHERE AssetID = %s AND ChapterName = %s",
                    (asset_id_binary, chapter_name)
                )

                # 刪除相關的權限映射
                for permission_chapter in existing_permission_chapters:
                    await cur.execute(
                        "DELETE FROM RolePermissionMappings WHERE AssetID = %s AND PermissionChapterID = %s",
                        (asset_id_binary, permission_chapter[0])
                    )

                # 如果 stage_settings 為空，則僅刪除相關設定並返回
                if not stage_settings:
                    await conn.commit()
                    return {"status": "success", "message": "已成功刪除該章節的所有審核設定"}

                # 插入新的工作流程階段
                for stage_order, stage in enumerate(stage_settings, start=1):
                    # 為每個階段生成獨立的權限章節ID
                    permission_chapter_id = uuid.uuid4().bytes
                    workflow_stage_id = uuid.uuid4().bytes
                    stage_name = stage.get("name")

                    await cur.execute("""
                        INSERT INTO WorkflowStages 
                        (WorkflowStageID, OrganizationID, AssetID, PermissionChapterID, 
                        ChapterName, StageOrder, StageName)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (workflow_stage_id, organization_id, asset_id_binary, 
                          permission_chapter_id, chapter_name, stage_order, stage_name))

                    # 插入審核人員權限映射
                    approver_groups = stage.get("approverGroups", [])
                    for group in approver_groups:
                        role_id = uuid.UUID(group.get("roleId")).bytes
                        await cur.execute("""
                            INSERT INTO RolePermissionMappings 
                            (RoleID, PermissionChapterID, AssetID, ResourceType, ActionType)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (role_id, permission_chapter_id, asset_id_binary, 
                              "stage", "read_write"))

                await conn.commit()
                
        return {"status": "success", "message": "工作流程階段保存成功"}

    except Exception as e:
        # 記錄錯誤
        print(f"Error in save_workflow_stage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 獲取章節的審核流程設定
@app.post("/api/report/get_workflow_stage")
async def get_workflow_stage(data: dict):
    try:
        # 獲取資產ID和章節名稱
        asset_id = data.get("assetID")
        chapter_name = data.get("chapterName")

        # 驗證必要參數
        if not all([asset_id, chapter_name]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的UUID轉換為二進制
        asset_id_binary = uuid.UUID(asset_id).bytes

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 查詢工作流程階段
                await cur.execute("""
                    SELECT ws.WorkflowStageID, ws.StageName, ws.StageOrder, ws.PermissionChapterID
                    FROM WorkflowStages ws
                    WHERE ws.AssetID = %s AND ws.ChapterName = %s
                    ORDER BY ws.StageOrder ASC
                """, (asset_id_binary, chapter_name))
                
                stages = await cur.fetchall()
                result = []

                for stage in stages:
                    workflow_stage_id = stage[0]
                    stage_name = stage[1]
                    permission_chapter_id = stage[3]

                    # 查詢每個階段的審核人員組
                    await cur.execute("""
                        SELECT r.RoleID, r.RoleName, r.Description, r.Color, r.CreatedAt
                        FROM RolePermissionMappings rpm
                        JOIN Roles r ON rpm.RoleID = r.RoleID
                        WHERE rpm.PermissionChapterID = %s AND rpm.AssetID = %s
                    """, (permission_chapter_id, asset_id_binary))
                    
                    approver_groups = []
                    roles = await cur.fetchall()
                    
                    for role in roles:
                        role_id = str(uuid.UUID(bytes=role[0]))
                        approver_groups.append({
                            "roleId": role_id,
                            "roleName": role[1],
                            "description": role[2],
                            "color": role[3],
                            "createdAt": role[4].strftime("%Y-%m-%dT%H:%M:%S") if role[4] else None
                        })

                    result.append({
                        "id": str(uuid.UUID(bytes=workflow_stage_id)),
                        "name": stage_name,
                        "approverGroups": approver_groups
                    })

                return {"status": "success", "data": result}

    except Exception as e:
        # 記錄錯誤
        print(f"Error in get_workflow_stage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 建立審核流程實例
@app.post("/api/report/create_workflow_instance")
async def create_workflow_instance(data: dict):
    # 傳入 AssetID, OrganizationID, ChapterName, userID
    asset_id = data.get("assetID")
    organization_id = data.get("organizationID")
    chapter_name = data.get("chapterName")
    user_id = data.get("userID")

    # 檢查必要參數
    if not all([asset_id, organization_id, chapter_name, user_id]):
        raise HTTPException(status_code=400, detail="缺少必要參數")

    # 連接資料庫
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                asset_binary = bytes.fromhex(asset_id.replace('-', ''))
                organization_id_binary = bytes.fromhex(organization_id.replace('-', ''))
                user_binary = bytes.fromhex(user_id.replace('-', ''))

                # 檢查是否已經建立審核流程階段
                # 去 workflowstages 取得 workflowstageid
                await cur.execute("SELECT WorkflowStageID FROM WorkflowStages WHERE AssetID = %s AND ChapterName = %s", (asset_binary, chapter_name))
                workflow_stage = await cur.fetchone()
                if not workflow_stage:
                    raise HTTPException(status_code=404, detail="尚未建立審核流程階段，無法送出審核")
                # workflow_stage = workflow_stage[0] 只用於檢查不需要使用

                # 檢查是否已存在審核中的流程實例
                check_query = """
                    SELECT WorkflowInstanceID, Status
                    FROM WorkflowInstances 
                    WHERE AssetID = %s
                    AND ChapterName = %s
                    AND Status IN ('審核中', '已退回', '已核准')
                """
                await cur.execute(check_query, (asset_binary, chapter_name))
                existing_workflow = await cur.fetchone()

                if existing_workflow:
                    if existing_workflow[1] == '審核中':
                        raise HTTPException(
                            status_code=400,
                            detail=f"該章節 '{chapter_name}' 已有審核中的流程實例"
                        )
                    elif existing_workflow[1] == '已退回':
                        # 更新 workflowinstances 的 Status 為 審核中
                        update_query = """
                            UPDATE `WorkflowInstances` SET `Status` = '審核中' WHERE `WorkflowInstanceID` = %s;
                        """
                        await cur.execute(update_query, (existing_workflow[0],))
                        await conn.commit()  # 添加事务提交

                        return {
                            "status": "success", 
                            "message": "已經有審核實例",
                            "data": {
                                "workflowInstanceID": str(uuid.UUID(bytes=existing_workflow[0]))
                            }
                        }
                    elif existing_workflow[1] == '已核准':
                        raise HTTPException(
                            status_code=400,
                            detail=f"該章節 '{chapter_name}' 已經核准"
                        )

                # 生成新的 UUID
                workflow_instance_id = str(uuid.uuid4())
                workflow_instance_id_binary = bytes.fromhex(workflow_instance_id.replace('-', ''))

                # 建立審核流程實例
                insert_query = """
                    INSERT INTO WorkflowInstances (
                        WorkflowInstanceID,
                        OrganizationID,
                        AssetID,
                        ChapterName,
                        Status,
                        CreatedBy
                    ) VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        '審核中',
                        %s
                    )
                """
                await cur.execute(insert_query, (
                    workflow_instance_id_binary,
                    organization_id_binary,
                    asset_binary,
                    chapter_name,
                    user_binary
                ))

                await conn.commit()

                return {
                    "status": "success",
                    "message": "成功建立審核流程實例",
                    "data": {
                        "workflowInstanceID": workflow_instance_id
                    }
                }

            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"建立審核流程實例失敗: {str(e)}")


# 建立送出審核資料
@app.post("/api/report/create_workflow_submit_data")
async def create_workflow_submit_data(data: dict):
    # 傳入 userID, SubmittedContent(json)
    user_id = data.get("userID")
    submitted_content = data.get("SubmittedContent")

    # 檢查必要參數
    if not all([user_id, submitted_content]):
        raise HTTPException(status_code=400, detail="缺少必要參數")

    # 連接資料庫
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # 生成新的 UUID 作為 BlockVersionID
                block_version_id = str(uuid.uuid4())
                block_version_binary = bytes.fromhex(block_version_id.replace('-', ''))
                user_binary = bytes.fromhex(user_id.replace('-', ''))

                # 將 submitted_content 轉換為 JSON 字符串
                if isinstance(submitted_content, str):
                    # 如果已經是字符串，確保它是有效的 JSON
                    try:
                        json.loads(submitted_content)
                    except json.JSONDecodeError:
                        raise HTTPException(status_code=400, detail="提交的內容不是有效的 JSON 格式")
                else:
                    # 如果是字典或列表，轉換為 JSON 字符串
                    submitted_content = json.dumps(submitted_content, ensure_ascii=False)

                # 插入資料到 ContentBlockVersions 表
                insert_query = """
                    INSERT INTO ContentBlockVersions (
                        BlockVersionID,
                        SubmittedContent,
                        ModifiedBy
                    ) VALUES (
                        %s,
                        %s,
                        %s
                    )
                """
                await cur.execute(insert_query, (
                    block_version_binary,
                    submitted_content,
                    user_binary
                ))

                await conn.commit()

                return {
                    "status": "success",
                    "message": "成功建立送審資料版本",
                    "data": {
                        "blockVersionID": block_version_id
                    }
                }

            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"建立送審資料版本失敗: {str(e)}")


# 建立送出審核記錄
@app.post("/api/report/create_workflow_submit_record")
async def create_workflow_submit_record(data: dict):
    # 傳入 WorkflowInstanceID, userID, BlockVersionID
    workflow_instance_id = data.get("workflowInstanceID")
    user_id = data.get("userID")
    block_version_id = data.get("blockVersionID")

    # 檢查必要參數
    if not all([workflow_instance_id, user_id, block_version_id]):
        raise HTTPException(status_code=400, detail="缺少必要參數")

    # 連接資料庫
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # 轉換 UUID 為 binary
                workflow_instance_binary = bytes.fromhex(workflow_instance_id.replace('-', ''))

                # 查詢工作流程實例資訊
                instance_query = """
                    SELECT AssetID, ChapterName
                    FROM WorkflowInstances 
                    WHERE WorkflowInstanceID = %s
                """
                await cur.execute(instance_query, (workflow_instance_binary,))
                instance_result = await cur.fetchone()

                if not instance_result:
                    raise HTTPException(status_code=404, detail="找不到對應的工作流程實例")

                asset_binary, chapter_name = instance_result

                # 查詢第一個階段的 WorkflowStageID
                stage_query = """
                    SELECT WorkflowStageID
                    FROM WorkflowStages 
                    WHERE AssetID = %s
                    AND ChapterName = %s
                    AND StageOrder = 1
                """
                await cur.execute(stage_query, (asset_binary, chapter_name))
                stage_result = await cur.fetchone()

                if not stage_result:
                    raise HTTPException(status_code=404, detail="找不到對應的工作流程階段")

                workflow_stage_binary = stage_result[0]

                # 先查詢 workflowstageinstances 表的 WorkflowInstanceID 是否存在
                await cur.execute("SELECT WorkflowInstanceID FROM WorkflowStageInstances WHERE WorkflowInstanceID = %s", (workflow_instance_binary,))
                workflow_instance_id_result = await cur.fetchone()
                if workflow_instance_id_result:
                    # 如果存在，則更新 workflowstageinstances 的 WorkflowStageID 為 第一階段
                    await cur.execute("UPDATE WorkflowStageInstances SET WorkflowStageID = %s WHERE WorkflowInstanceID = %s", (workflow_stage_binary, workflow_instance_binary))
                    await conn.commit()
                    return {
                        "status": "success",
                        "message": "已經更新現有的審核實例",
                        "data": {}
                    }

                # 如果 workflowstageinstances 表的 WorkflowInstanceID 不存在，則建立新的審核實例
                # 生成新的 UUID 作為 WorkflowInstanceStageID
                workflow_instance_stage_id = str(uuid.uuid4())
                workflow_instance_stage_binary = bytes.fromhex(workflow_instance_stage_id.replace('-', ''))
                user_binary = bytes.fromhex(user_id.replace('-', ''))
                block_version_binary = bytes.fromhex(block_version_id.replace('-', ''))

                # 建立工作流程階段實例記錄
                insert_query = """
                    INSERT INTO WorkflowStageInstances (
                        WorkflowInstanceStageID,
                        WorkflowInstanceID,
                        WorkflowStageID,
                        SubmitterID,
                        BlockVersionID
                    ) VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                """
                await cur.execute(insert_query, (
                    workflow_instance_stage_binary,
                    workflow_instance_binary,
                    workflow_stage_binary,
                    user_binary,
                    block_version_binary
                ))

                await conn.commit()

                # 將 binary 轉回 UUID 字符串用於返回
                workflow_stage_id = uuid.UUID(bytes=workflow_stage_binary).hex
                workflow_stage_id = f"{workflow_stage_id[:8]}-{workflow_stage_id[8:12]}-{workflow_stage_id[12:16]}-{workflow_stage_id[16:20]}-{workflow_stage_id[20:]}"

                return {
                    "status": "success",
                    "message": "成功建立送審記錄",
                    "data": {
                        "workflowInstanceStageID": workflow_instance_stage_id,
                        "workflowStageID": workflow_stage_id
                    }
                }

            except HTTPException as he:
                await conn.rollback()
                raise he
            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"建立送審記錄失敗: {str(e)}")


# 獲取待審核列表
@app.post("/api/report/get_pending_reviews")
async def get_pending_reviews(data: dict):
    try:
        # 獲取必要參數
        user_id = data.get("userID")
        if not user_id:
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 將字符串格式的user_id轉換為BINARY(16)格式
        try:
            user_id_binary = uuid.UUID(user_id).bytes
        except ValueError:
            raise HTTPException(status_code=400, detail="無效的用戶ID格式")

        # 連接資料庫
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 開始事務
                    await conn.begin()

                    # 1. 獲取用戶的所有角色
                    await cur.execute("""
                        SELECT DISTINCT ur.RoleID
                        FROM UserRoles ur
                        WHERE ur.UserID = %s
                    """, (user_id_binary,))
                    role_ids = await cur.fetchall()
                    # print("role_ids", role_ids)
                    
                    if not role_ids:
                        return {"status": "success", "data": []}

                    # 2. 獲取這些角色對應的審核權限
                    role_ids_list = [role[0] for role in role_ids]
                    placeholders = ', '.join(['%s'] * len(role_ids_list))
                    
                    await cur.execute(f"""
                        SELECT DISTINCT rpm.PermissionChapterID
                        FROM RolePermissionMappings rpm
                        WHERE rpm.RoleID IN ({placeholders})
                        AND rpm.ResourceType = 'stage'
                    """, tuple(role_ids_list))
                    
                    permission_chapters = await cur.fetchall()
                    # print("permission_chapters", permission_chapters)
                    
                    if not permission_chapters:
                        return {"status": "success", "data": []}

                    # 3. 獲取對應的工作流程階段
                    permission_chapters_list = [pc[0] for pc in permission_chapters]
                    placeholders = ', '.join(['%s'] * len(permission_chapters_list))
                    
                    await cur.execute(f"""
                        SELECT DISTINCT ws.WorkflowStageID
                        FROM WorkflowStages ws
                        WHERE ws.PermissionChapterID IN ({placeholders})
                    """, tuple(permission_chapters_list))
                    
                    workflow_stages = await cur.fetchall()
                    
                    if not workflow_stages:
                        return {"status": "success", "data": []}

                    # 4. 獲取待審核的實例
                    workflow_stages_list = [ws[0] for ws in workflow_stages]
                    placeholders = ', '.join(['%s'] * len(workflow_stages_list))
                    
                    await cur.execute(f"""
                        SELECT 
                            wi.WorkflowInstanceID,
                            wi.AssetID,
                            wi.ChapterName,
                            wsi.WorkflowStageID,
                            wsi.SubmitterID,
                            wsi.BlockVersionID,
                            wsi.SubmittedAt,
                            oa.AssetName,
                            u.UserName as SubmitterName
                        FROM WorkflowStageInstances wsi
                        JOIN WorkflowInstances wi ON wsi.WorkflowInstanceID = wi.WorkflowInstanceID
                        JOIN OrganizationAssets oa ON wi.AssetID = oa.AssetID
                        JOIN Users u ON wsi.SubmitterID = u.UserID
                        WHERE wsi.WorkflowStageID IN ({placeholders})
                        ORDER BY wsi.SubmittedAt DESC
                    """, tuple(workflow_stages_list))
                    
                    reviews = await cur.fetchall()
                    
                    # 格式化返回數據
                    review_list = []
                    for review in reviews:
                        review_list.append({
                            "title": f"{review[7]} - {review[2]}", # AssetName - ChapterName
                            "workflow_instance_id": uuid.UUID(bytes=review[0]).hex,
                            "workflow_stage_id": uuid.UUID(bytes=review[3]).hex,
                            "block_version_id": uuid.UUID(bytes=review[5]).hex,
                            "submitter": review[8],  # SubmitterName
                            "submitted_at": review[6].isoformat() if review[6] else None
                        })

                    await conn.commit()
                    # print("review_list", review_list)
                    return {
                        "status": "success",
                        "data": review_list
                    }

                except Exception as e:
                    await conn.rollback()
                    print(f"數據庫操作失敗: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"獲取待審核列表失敗: {str(e)}")

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"未預期的錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# 取得送審資料
@app.post("/api/report/get_submitted_data")
async def get_submitted_data(data: dict):
    try:
        workflow_instance_id = data.get("workflowInstanceID")
        if not workflow_instance_id:
            return {"status": "error", "message": "缺少必要參數 workflowInstanceID"}

        # 連接資料庫
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 查詢最新的 WorkflowStageInstance
                query = """
                    SELECT wsi.BlockVersionID, cbv.SubmittedContent
                    FROM WorkflowStageInstances wsi
                    LEFT JOIN ContentBlockVersions cbv ON wsi.BlockVersionID = cbv.BlockVersionID
                    WHERE wsi.WorkflowInstanceID = UNHEX(%s)
                    ORDER BY wsi.SubmittedAt DESC
                    LIMIT 1
                """
                await cur.execute(query, (workflow_instance_id.replace('-', ''),))
                result = await cur.fetchone()

                if not result:
                    return {"status": "error", "message": "找不到相關的送審資料"}

                block_version_id, submitted_content = result

                if not submitted_content:
                    return {"status": "error", "message": "送審內容為空"}
                
                # print("submitted_content:", submitted_content)

                return {
                    "status": "success",
                    "data": {
                        "blockVersionID": block_version_id.hex() if block_version_id else None,
                        "submittedContent": submitted_content
                    }
                }

    except Exception as e:
        print(f"Error in get_submitted_data: {str(e)}")
        return {"status": "error", "message": f"獲取送審資料時發生錯誤: {str(e)}"}


# 提交審核結果
@app.post("/api/report/submit_review")
async def submit_review(data: dict):
    try:
        workflow_instance_id = data.get('WorkflowInstanceID')
        reviewer_id = data.get('ReviewerID')
        review_action = data.get('ReviewAction')
        review_comment = data.get('ReviewComment')
        block_version_id = data.get('BlockVersionID')

        # 參數驗證
        if not all([workflow_instance_id, reviewer_id, review_action, block_version_id]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        if review_action not in ['approved', 'rejected', 'recalled']:
            raise HTTPException(status_code=400, detail="無效的審核動作")

        # 連接資料庫
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:

                workflow_instance_id_binary = bytes.fromhex(workflow_instance_id.replace('-', ''))
                reviewer_id_binary = bytes.fromhex(reviewer_id.replace('-', ''))
                block_version_id_binary = bytes.fromhex(block_version_id.replace('-', ''))

                # 獲取當前階段資訊
                await cur.execute("""
                    SELECT ws.WorkflowStageID, ws.AssetID, ws.ChapterName, ws.StageOrder, ws.OrganizationID
                    FROM WorkflowStageInstances wsi
                    JOIN WorkflowStages ws ON wsi.WorkflowStageID = ws.WorkflowStageID
                    WHERE wsi.WorkflowInstanceID = %s
                """, (workflow_instance_id_binary,))
                current_stage = await cur.fetchone()

                if not current_stage:
                    raise HTTPException(status_code=404, detail="找不到對應的審核流程階段")

                current_stage_id, asset_id, chapter_name, stage_order, organization_id = current_stage

                # 記錄審核日誌
                approval_log_id = uuid.uuid4()
                await cur.execute("""
                    INSERT INTO StageApprovalLogs (
                        ApprovalStageLogID, WorkflowInstanceID, WorkflowStageID,
                        ReviewerID, ReviewAction, ReviewComments,
                        ReviewedAt, BlockVersionID
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s, %s,
                        CURRENT_TIMESTAMP, %s
                    )
                """, (
                    approval_log_id, workflow_instance_id_binary, current_stage_id,
                    reviewer_id_binary, review_action, review_comment,
                    block_version_id_binary
                ))

                # 處理審核動作
                next_stage_order = 1 if review_action == 'rejected' else stage_order + 1

                # 如果是拒絕，更新工作流實例狀態
                if review_action == 'rejected':
                    await cur.execute("""
                        UPDATE WorkflowInstances 
                        SET Status = '已退回', UpdatedAt = CURRENT_TIMESTAMP
                        WHERE WorkflowInstanceID = %s
                    """, (workflow_instance_id_binary,))

                    # 更新 workflowstageinstances 的 WorkflowStageID 為 NULL
                    await cur.execute("""
                        UPDATE WorkflowStageInstances 
                        SET WorkflowStageID = NULL, LastUpdatedAt = CURRENT_TIMESTAMP
                        WHERE WorkflowInstanceID = %s
                    """, (workflow_instance_id_binary,))
                    await conn.commit()
                    return {"message": "已退回修改", "status": "rejected"}

                # 查詢下一個階段
                await cur.execute("""
                    SELECT WorkflowStageID 
                    FROM WorkflowStages 
                    WHERE AssetID = %s 
                    AND ChapterName = %s 
                    AND StageOrder = %s
                """, (asset_id, chapter_name, next_stage_order))
                next_stage = await cur.fetchone()

                # 如果沒有下一個階段，完成審核流程
                if not next_stage and review_action == 'approved':
                    await complete_review(conn, workflow_instance_id_binary)
                    await conn.commit()
                    return {"message": "審核流程已完成", "status": "completed"}

                # 更新工作流階段實例
                if next_stage:
                    await cur.execute("""
                        UPDATE WorkflowStageInstances 
                        SET WorkflowStageID = %s, 
                            LastUpdatedAt = CURRENT_TIMESTAMP
                        WHERE WorkflowInstanceID = %s
                    """, (next_stage[0], workflow_instance_id_binary))

                await conn.commit()

                return {
                    "message": "審核結果已提交",
                    "next_stage": next_stage[0].hex() if next_stage else None,
                    "status": "success"
                }

    except Exception as e:
        # 記錄錯誤
        print(f"提交審核結果時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"提交審核結果時發生錯誤: {str(e)}")


# 完成審核流程的輔助函數
async def complete_review(conn, workflow_instance_id_binary):
    """完成審核流程的輔助函數"""
    async with conn.cursor() as cur:
        # 更新工作流實例狀態
        await cur.execute("""
            UPDATE WorkflowInstances 
            SET Status = '已核准',
                EndTime = CURRENT_TIMESTAMP,
                UpdatedAt = CURRENT_TIMESTAMP
            WHERE WorkflowInstanceID = %s
        """, (workflow_instance_id_binary,))

        # 更新 workflowstageinstances 的 WorkflowStageID 為 NULL
        await cur.execute("""
            UPDATE WorkflowStageInstances 
            SET WorkflowStageID = NULL, 
                LastUpdatedAt = CURRENT_TIMESTAMP
            WHERE WorkflowInstanceID = %s
        """, (workflow_instance_id_binary,))


# 獲取審核流程和進度
@app.post("/api/report/get_review_progress")
async def get_review_progress(data: dict):
    try:
        # 獲取並驗證 workflowInstanceID
        workflow_instance_id = data.get('workflowInstanceID')
        if not workflow_instance_id:
            raise HTTPException(status_code=400, detail="缺少必要參數 workflowInstanceID")

        # 將 UUID 轉換為二進制格式
        workflow_instance_id_bin = bytes.fromhex(workflow_instance_id.replace('-', ''))

        # 連接資料庫
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # 1. 查詢當前工作流實例的基本信息
                await cur.execute("""
                    SELECT wi.*, wsi.WorkflowStageID, ws.StageOrder, ws.StageName, ws.AssetID, ws.ChapterName
                    FROM WorkflowInstances wi
                    LEFT JOIN WorkflowStageInstances wsi ON wi.WorkflowInstanceID = wsi.WorkflowInstanceID
                    LEFT JOIN WorkflowStages ws ON wsi.WorkflowStageID = ws.WorkflowStageID
                    WHERE wi.WorkflowInstanceID = %s
                    ORDER BY wsi.SubmittedAt DESC
                    LIMIT 1
                """, (workflow_instance_id_bin,))
                
                current_workflow = await cur.fetchone()
                if not current_workflow:
                    raise HTTPException(status_code=404, detail="找不到指定的審核流程")

                # 2. 查詢該章節的所有審核階段
                await cur.execute("""
                    SELECT StageOrder, StageName
                    FROM WorkflowStages
                    WHERE AssetID = %s AND ChapterName = %s
                    ORDER BY StageOrder
                """, (current_workflow['AssetID'], current_workflow['ChapterName']))
                
                all_stages = await cur.fetchall()

                # 構建返回數據
                response_data = {
                    "currentStage": {
                        "stageOrder": current_workflow['StageOrder'],
                        "stageName": current_workflow['StageName']
                    },
                    "allStages": [
                        {
                            "stageOrder": stage['StageOrder'],
                            "stageName": stage['StageName']
                        }
                        for stage in all_stages
                    ],
                    "workflowStatus": current_workflow['Status']
                }

                return {
                    "status_code": 200,
                    "content": {
                        "code": 200,
                        "message": "成功獲取審核進度",
                        "data": response_data
                    }
                }

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in get_review_progress: {str(e)}")
        raise HTTPException(status_code=500, detail="獲取審核進度時發生錯誤")


if __name__ == "__main__":
    uvicorn.run("chatESG_FastAPI:app", host="0.0.0.0", port=8000, reload=True)

# python -m http.server 8001 --bind 127.0.0.1
