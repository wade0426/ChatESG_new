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
            
            # 將BINARY(16)格式的UUID轉換為字符串
            user_id_str = uuid.UUID(bytes=user[0]).hex if user[0] else None
            organization_id_str = uuid.UUID(bytes=user[3]).hex if user[3] else None
            
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
                    "lastLoginAt": user[7].isoformat() if user[7] else None
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
                organization_code = str(uuid.uuid4())[:8].upper()
                
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


# 加入組織
@app.post("/api/organizations/join")
async def join_organization(join_data: dict):
    try:
        # 將字符串格式的user_id轉換為BINARY(16)格式
        user_id = uuid.UUID(join_data.get("user_id")).bytes
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="無效的用戶ID格式")
    
    organization_code = join_data.get("organization_code")
    
    if not organization_code:
        raise HTTPException(status_code=400, detail="缺少必要參數")
    
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # 開始事務
                await conn.begin()
                
                # 檢查用戶是否已經在組織中
                await cur.execute("SELECT OrganizationID FROM Users WHERE UserID = %s", (user_id,))
                user = await cur.fetchone()
                if user and user[0]:
                    raise HTTPException(status_code=400, detail="使用者已經在其他組織中")
                
                # 查找組織代碼對應的組織
                await cur.execute(
                    "SELECT OrganizationID FROM Organizations WHERE OrganizationCode = %s",
                    (organization_code,)
                )
                organization = await cur.fetchone()
                
                if not organization:
                    raise HTTPException(status_code=404, detail="無效的組織代碼")
                
                # 檢查是否已經是組織成員
                await cur.execute(
                    "SELECT OrganizationMemberID FROM OrganizationMembers WHERE OrganizationID = %s AND UserID = %s",
                    (organization[0], user_id)
                )
                if await cur.fetchone():
                    raise HTTPException(status_code=400, detail="使用者已經是該組織的成員")
                
                # 更新用戶的組織ID
                await cur.execute(
                    "UPDATE Users SET OrganizationID = %s WHERE UserID = %s",
                    (organization[0], user_id)
                )

                # 更新組織成員資料表
                await cur.execute("""
                    INSERT INTO OrganizationMembers 
                    (OrganizationID, UserID, CreatedAt) 
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                """, (organization[0], user_id))

                # 為新成員分配預設角色（一般）
                await cur.execute("""
                    SELECT RoleID FROM Roles 
                    WHERE OrganizationID = %s AND RoleName = '一般'
                """, (organization[0],))
                default_role = await cur.fetchone()
                
                if default_role:
                    await cur.execute("""
                        INSERT INTO UserRoles (UserID, RoleID, OrganizationID)
                        VALUES (%s, %s, %s)
                    """, (user_id, default_role[0], organization[0]))
                
                # 提交事務
                await conn.commit()
                
                return {"status": "success", "message": "成功加入組織"}
                
            except Exception as e:
                # 發生錯誤時回滾事務
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"加入組織失敗: {str(e)}")


@app.post("/api/organizations/info")
async def get_organization_info(data: dict):
    organization_id = data.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=400, detail="缺少組織ID")
    
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
                    u.UserName as OwnerName,
                    (SELECT COUNT(*) FROM OrganizationMembers WHERE OrganizationID = o.OrganizationID) as MemberCount
                FROM Organizations o
                LEFT JOIN Users u ON o.OwnerID = u.UserID
                WHERE o.OrganizationID = %s
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
                    GROUP_CONCAT(r.RoleName) as Roles,
                    om.CreatedAt
                FROM OrganizationMembers om
                JOIN Users u ON om.UserID = u.UserID
                LEFT JOIN UserRoles ur ON ur.UserID = u.UserID AND ur.OrganizationID = om.OrganizationID
                LEFT JOIN Roles r ON r.RoleID = ur.RoleID
                WHERE om.OrganizationID = %s
                GROUP BY u.UserID
            """, (organization_id,))
            
            members = await cur.fetchall()
            members_list = []
            for member in members:
                roles = member[4].split(',') if member[4] else []
                members_list.append({
                    "userID": member[0],
                    "name": member[1],
                    "avatarUrl": member[2],
                    "email": member[3],
                    "roles": roles,
                    "joinedAt": member[5].isoformat() if member[5] else None
                })
            
            # 獲取組織的所有可用角色
            await cur.execute("""
                SELECT RoleName
                FROM Roles
                WHERE OrganizationID = %s
                ORDER BY CreatedAt
            """, (organization_id,))
            
            available_roles = [role[0] for role in await cur.fetchall()]
            
            return {
                "status": "success",
                "data": {
                    "id": org[0],
                    "name": org[1],
                    "description": org[2],
                    "avatarUrl": org[3],
                    "code": org[4],
                    "owner": {
                        "id": org[5],
                        "name": org[11]
                    },
                    "purchaseType": org[6],
                    "apiCallQuota": org[7],
                    "maxMembers": org[8],
                    "roles": available_roles,
                    "memberCount": org[12],
                    "members": members_list,
                    "createdAt": org[9].isoformat() if org[9] else None,
                    "updatedAt": org[10].isoformat() if org[10] else None
                }
            }


@app.post("/api/organizations/get_by_user")
async def get_organization_by_user(data: dict):
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="缺少用戶ID")
    
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT om.OrganizationID, o.OrganizationName
                FROM OrganizationMembers om
                LEFT JOIN Organizations o ON om.OrganizationID = o.OrganizationID
                WHERE om.UserID = %s
            """, (user_id,))
            
            result = await cur.fetchone()
            if not result:
                return {"status": "success", "data": None}
            
            return {
                "status": "success",
                "data": {
                    "organization_id": result[0],
                    "organization_name": result[1]
                }
            }


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
                """, (user_id, organization_id))
                
                if not await cur.fetchone():
                    raise HTTPException(status_code=404, detail="找不到該組織成員")
                
                # 刪除用戶現有的角色
                await cur.execute("""
                    DELETE FROM UserRoles 
                    WHERE UserID = %s AND OrganizationID = %s
                """, (user_id, organization_id))
                
                # 獲取角色ID並添加新的角色
                for role_name in roles:
                    # 檢查角色是否存在，如果不存在則創建
                    await cur.execute("""
                        SELECT RoleID 
                        FROM Roles 
                        WHERE OrganizationID = %s AND RoleName = %s
                    """, (organization_id, role_name))
                    
                    role = await cur.fetchone()
                    if not role:
                        # 如果角色不存在，創建新角色
                        role_id = uuid.uuid4().bytes
                        await cur.execute("""
                            INSERT INTO Roles (RoleID, OrganizationID, RoleName)
                            VALUES (%s, %s, %s)
                        """, (role_id, organization_id, role_name))
                    else:
                        role_id = role[0]
                    
                    # 添加用戶角色關聯
                    await cur.execute("""
                        INSERT INTO UserRoles (UserID, RoleID, OrganizationID)
                        VALUES (%s, %s, %s)
                    """, (user_id, role_id, organization_id))
                
                await conn.commit()
                return {"status": "success", "message": "成員身份組更新成功"}
                
            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"更新失敗: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("chatESG_FastAPI:app", host="0.0.0.0", port=8000, reload=True)