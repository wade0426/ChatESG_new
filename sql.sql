-- --------------------------------------------------------
-- 資料庫名稱：ChatESG_new
-- 創建時間：{當前日期}
-- 資料庫說明：ESG 永續報告書生成系統資料庫
-- --------------------------------------------------------

-- 創建資料庫（如果不存在）
CREATE DATABASE IF NOT EXISTS ChatESG_new
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 選擇要使用的資料庫
USE ChatESG_new;

-- --------------------------------------------------------
-- 使用者資料表
-- 用於存儲系統用戶的基本信息
-- --------------------------------------------------------
CREATE TABLE Users (
    UserID BINARY(16) PRIMARY KEY COMMENT '使用者唯一標識 (UUID)',
    UserName VARCHAR(100) NOT NULL COMMENT '使用者名稱',
    UserPassword VARCHAR(255) NOT NULL COMMENT '使用者密碼（使用 bcrypt 或 Argon2 加密）',
    UserEmail VARCHAR(100) NOT NULL UNIQUE COMMENT '使用者電子郵件（用於登錄和通知）',
    AvatarUrl VARCHAR(255) COMMENT '使用者頭像URL',
    OrganizationID BINARY(16) DEFAULT NULL COMMENT '使用者所屬組織(UUID)',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最後更新時間',
    LastLoginAt TIMESTAMP COMMENT '最後登入時間',
    LoginAttempts INT DEFAULT 0 COMMENT '登入嘗試次數',
    AccountStatus ENUM('active', 'locked', 'disabled') DEFAULT 'active' COMMENT '帳號狀態',
    PasswordChangedAt TIMESTAMP COMMENT '密碼最後修改時間'
) COMMENT '使用者基本資料表';

-- --------------------------------------------------------
-- 組織資料表
-- 用於管理不同的組織及其基本信息
-- --------------------------------------------------------
CREATE TABLE Organizations (
    OrganizationID BINARY(16) PRIMARY KEY COMMENT '組織唯一標識 (UUID)',
    OrganizationName VARCHAR(100) NOT NULL COMMENT '組織名稱',
    OrganizationCode VARCHAR(8) NOT NULL UNIQUE COMMENT '組織加入代碼（8位大小寫字母和數字）',
    OrganizationDescription VARCHAR(255) COMMENT '組織描述',
    AvatarUrl VARCHAR(255) COMMENT '組織標誌URL',
    OwnerID BINARY(16) DEFAULT NULL COMMENT '組織擁有者(UUID)',
    PurchaseType ENUM('Free', 'Basic', 'Pro', 'Premium', 'Enterprise', 'Test') NOT NULL COMMENT '組織的購買類型',
    APICallQuota INT DEFAULT 10000 COMMENT 'API 呼叫配額',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最後更新時間',
    IsDeleted BOOLEAN DEFAULT FALSE COMMENT '是否已刪除',
    DeletedAt TIMESTAMP NULL DEFAULT NULL COMMENT '刪除時間（軟刪除）',
    FOREIGN KEY (OwnerID) REFERENCES Users(UserID) ON DELETE RESTRICT
) COMMENT '組織資料表';

-- --------------------------------------------------------
-- 組織成員資料表
-- 用於管理組織與成員之間的關係
-- --------------------------------------------------------
CREATE TABLE OrganizationMembers (
    OrganizationMemberID INT AUTO_INCREMENT PRIMARY KEY COMMENT '組織成員關係唯一標識(ID)',
    OrganizationID BINARY(16) NOT NULL COMMENT '組織(UUID)',
    UserID BINARY(16) NOT NULL COMMENT '使用者(UUID)',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '加入時間',
    FOREIGN KEY (OrganizationID) REFERENCES Organizations(OrganizationID) ON DELETE CASCADE,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    UNIQUE KEY unique_member_organization (OrganizationID, UserID)
) COMMENT '組織成員資料表';

-- --------------------------------------------------------
-- 角色資料表
-- 用於定義系統中的角色
-- --------------------------------------------------------
CREATE TABLE Roles (
    RoleID BINARY(16) PRIMARY KEY COMMENT '角色唯一標識(UUID)',
    OrganizationID BINARY(16) NOT NULL COMMENT '組織(UUID)',
    RoleName VARCHAR(50) NOT NULL COMMENT '角色名稱',
    Description VARCHAR(255) COMMENT '角色描述',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    FOREIGN KEY (OrganizationID) REFERENCES Organizations(OrganizationID) ON DELETE CASCADE
) COMMENT '角色資料表';

-- --------------------------------------------------------
-- 使用者角色關聯表
-- 用於管理使用者在組織中的多重角色
-- --------------------------------------------------------
CREATE TABLE UserRoles (
    UserID BINARY(16) NOT NULL COMMENT '使用者(UUID)',
    RoleID BINARY(16) NOT NULL COMMENT '角色(UUID)',
    OrganizationID BINARY(16) NOT NULL COMMENT '組織(UUID)',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    PRIMARY KEY (UserID, RoleID, OrganizationID),
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    FOREIGN KEY (RoleID) REFERENCES Roles(RoleID) ON DELETE CASCADE,
    FOREIGN KEY (OrganizationID) REFERENCES Organizations(OrganizationID) ON DELETE CASCADE
) COMMENT '使用者角色關聯表';

-- --------------------------------------------------------
-- 角色權限映射表
-- 用於管理角色與權限之間的映射關係
-- --------------------------------------------------------
CREATE TABLE RolePermissionMappings (
    RoleID BINARY(16) NOT NULL COMMENT '角色(UUID)',
    PermissionID BINARY(16) NOT NULL COMMENT '權限(UUID)',
    ChapterUUID BINARY(16) DEFAULT NULL COMMENT '章節權限識別標籤(UUID)',
    ResourceType VARCHAR(50) DEFAULT 'report/template/company_info' COMMENT '資源類型',
    ActionType VARCHAR(50) DEFAULT 'read' COMMENT '操作類型', -- 例如：read/read_write/no_access/create/update/delete
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    PRIMARY KEY (RoleID, PermissionID),
    FOREIGN KEY (RoleID) REFERENCES Roles(RoleID) ON DELETE CASCADE,
    FOREIGN KEY (PermissionID) REFERENCES Permissions(PermissionID) ON DELETE CASCADE
) COMMENT '角色權限映射表';

-- --------------------------------------------------------
-- 組織資產資料表
-- 用於管理組織的資產資料
-- --------------------------------------------------------
CREATE TABLE OrganizationAssets (
    AssetID BINARY(16) PRIMARY KEY COMMENT '資產唯一標識(UUID)',
    OrganizationID BINARY(16) NOT NULL COMMENT '組織(UUID)',
    AssetName VARCHAR(100) NOT NULL COMMENT '資產名稱',
    AssetType ENUM('report', 'template', 'company_info') NOT NULL COMMENT '資產類型',
    CreatorID BINARY(16) COMMENT '資產創建者(UUID)',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間',
    Status ENUM('editing', 'archived') NOT NULL DEFAULT 'editing' COMMENT '資產狀態',
    AccessPermissions JSON COMMENT '資產存取權限',
    Content JSON COMMENT '資產內容(章節, 內容UUID)',
    IsDeleted BOOLEAN DEFAULT FALSE COMMENT '是否已刪除',
    DeletedAt TIMESTAMP NULL DEFAULT NULL COMMENT '刪除時間（軟刪除）',
    FOREIGN KEY (OrganizationID) REFERENCES Organizations(OrganizationID) ON DELETE RESTRICT,
    FOREIGN KEY (CreatorID) REFERENCES Users(UserID) ON DELETE SET NULL
) COMMENT '組織資產資料表';

-- --------------------------------------------------------
-- 組織資產內容資料表
-- --------------------------------------------------------
CREATE TABLE ReportContentBlocks (
    BlockID BINARY(16) PRIMARY KEY COMMENT '內容(UUID)',
    status ENUM('editing', 'archived') NOT NULL DEFAULT 'editing' COMMENT '內容狀態',
    content JSON COMMENT '內容(文字、圖片、內容檢驗、註解)',
    LastModified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最後修改時間',
    ModifiedBy BINARY(16) DEFAULT NULL COMMENT '內容修改者(UUID)',
    IsLocked BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否被鎖定',
    LockedBy BINARY(16) DEFAULT NULL COMMENT '鎖定者(UUID)',
    LockedAt TIMESTAMP DEFAULT NULL COMMENT '鎖定時間',
    version INT DEFAULT 1
) COMMENT '組織資產內容資料表';

-- 在所有表創建完成後加入外鍵約束
-- 保護組織不會因為擁有者被刪除而消失，同時允許組織解散後讓用戶保持獨立狀態(NULL)
ALTER TABLE Users
ADD CONSTRAINT fk_user_organization
FOREIGN KEY (OrganizationID) REFERENCES Organizations(OrganizationID) ON DELETE SET NULL;

-- 建議加入索引
ALTER TABLE Users ADD INDEX idx_email (UserEmail);
ALTER TABLE Users ADD INDEX idx_org (OrganizationID);
ALTER TABLE Users ADD INDEX idx_login_status (AccountStatus, LastLoginAt);
ALTER TABLE OrganizationMembers ADD INDEX idx_user (UserID);
ALTER TABLE OrganizationMembers ADD INDEX idx_org (OrganizationID);
ALTER TABLE OrganizationAssets ADD INDEX idx_org_type (OrganizationID, AssetType);
ALTER TABLE OrganizationAssets ADD INDEX idx_creator (CreatorID, CreatedAt);
ALTER TABLE ReportContentBlocks ADD INDEX idx_status (status);
ALTER TABLE ReportContentBlocks ADD INDEX idx_modified (LastModified);
ALTER TABLE RolePermissions ADD INDEX idx_role_permission (RoleID, PermissionType);
ALTER TABLE Roles ADD INDEX idx_org_role (OrganizationID, RoleName);

-- 建議加入的複合索引
ALTER TABLE OrganizationAssets 
ADD INDEX idx_org_status_type_cover (OrganizationID, Status, AssetType)
INCLUDE (AssetName, CreatorID, CreatedAt);
ALTER TABLE ReportContentBlocks ADD INDEX idx_status_version (Status, Version);
ALTER TABLE UserRoles ADD INDEX idx_org_role (OrganizationID, RoleID);