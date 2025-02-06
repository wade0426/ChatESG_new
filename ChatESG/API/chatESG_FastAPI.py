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
                        json.dumps({}),  # 空的內容，表示剛建立還沒有選擇準則
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






if __name__ == "__main__":
    uvicorn.run("chatESG_FastAPI:app", host="0.0.0.0", port=8000, reload=True)
