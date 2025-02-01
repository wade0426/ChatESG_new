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
                       o.OrganizationName, u.AccountStatus, u.LastLoginAt
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
                    "organizationRoles": user_roles
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
            """, (organization_id,))
            
            org = await cur.fetchone()
            if not org:
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
            """, (organization_id,))
            
            members = await cur.fetchall()
            members_list = []
            for member in members:
                # 單獨查詢每個成員的角色
                await cur.execute("""
                    SELECT DISTINCT r.RoleName, r.Color
                    FROM UserRoles ur
                    JOIN Roles r ON r.RoleID = ur.RoleID
                    WHERE ur.UserID = %s AND ur.OrganizationID = %s
                    ORDER BY r.CreatedAt
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
                ORDER BY CreatedAt
            """, (organization_id,))
            
            available_roles = [{"roleName": role[0], "roleColor": role[1]} for role in await cur.fetchall()]
            
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
            await cur.execute("""
                SELECT o.OrganizationID, o.OrganizationName, o.OrganizationCode, o.AvatarUrl
                FROM OrganizationMembers om
                LEFT JOIN Organizations o ON om.OrganizationID = o.OrganizationID
                WHERE om.UserID = %s AND o.IsDeleted = FALSE
            """, (user_id,))
            
            result = await cur.fetchone()
            if not result:
                return {"status": "success", "data": None}
            
            return {
                "status": "success",
                "data": {
                    "organization_id": uuid.UUID(bytes=result[0]).hex,
                    "organization_name": result[1],
                    "organization_code": result[2],
                    "avatar_url": result[3] or DEFAULT_ORGANIZATION_LOGO
                }
            }


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

    uvicorn.run("chatESG_FastAPI:app", host="0.0.0.0", port=8000, reload=True)