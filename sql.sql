-- --------------------------------------------------------
-- 資料庫名稱：ChatESG_new
-- 創建時間：{當前日期}
-- 資料庫說明：ESG 永續報告書生成系統資料庫
-- 資料庫版本：10.4.32-MariaDB
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
    UserName VARCHAR(100) NOT NULL UNIQUE COMMENT '使用者名稱',
    UserPassword VARCHAR(255) NOT NULL COMMENT '使用者密碼（使用 bcrypt 或 Argon2 加密）',
    UserEmail VARCHAR(100) NOT NULL UNIQUE COMMENT '使用者電子郵件',
    AvatarUrl VARCHAR(255) COMMENT '使用者頭像URL',
    OrganizationID BINARY(16) DEFAULT NULL COMMENT '使用者所屬組織(UUID)',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最後更新時間',
    LastLoginAt TIMESTAMP(6) COMMENT '最後登入時間',
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
    OrganizationCode CHAR(8) COLLATE utf8mb4_bin NOT NULL UNIQUE COMMENT '組織加入代碼（8位大小寫字母和數字）',
    OrganizationDescription VARCHAR(255) COMMENT '組織描述',
    AvatarUrl VARCHAR(255) COMMENT '組織標誌URL',
    OwnerID BINARY(16) DEFAULT NULL COMMENT '組織擁有者(UUID)',
    PurchaseType ENUM('Free', 'Basic', 'Pro', 'Premium', 'Enterprise', 'Test') NOT NULL COMMENT '組織的購買類型',
    APICallQuota INT DEFAULT 10000 COMMENT 'API 呼叫配額',
    MaxMembers INT DEFAULT 5 COMMENT '最大成員數限制',
    ExpiryDate TIMESTAMP NULL COMMENT '訂閱到期時間',
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
    PermissionChapterID BINARY(16) DEFAULT NULL COMMENT '章節權限識別標籤(UUID)',
    ResourceType VARCHAR(50) DEFAULT 'report/template/company_info' COMMENT '資源類型',
    ActionType ENUM('read', 'read_write', 'no_access', 'create', 'update', 'delete') DEFAULT 'read' COMMENT '操作類型',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    PRIMARY KEY (RoleID),
    FOREIGN KEY (RoleID) REFERENCES Roles(RoleID) ON DELETE CASCADE
) COMMENT '角色權限映射表';

-- --------------------------------------------------------
-- 組織資產資料表
-- 用於管理組織的資產資料
-- --------------------------------------------------------
CREATE TABLE OrganizationAssets (
    AssetID BINARY(16) PRIMARY KEY COMMENT '資產唯一標識(UUID)',
    OrganizationID BINARY(16) NOT NULL COMMENT '組織(UUID)',
    AssetName VARCHAR(100) NOT NULL COMMENT '資產名稱',
    AssetType ENUM('report', 'standard_template', 'company_info') NOT NULL COMMENT '資產類型',
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
    LastModified TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最後修改時間',
    ModifiedBy BINARY(16) DEFAULT NULL COMMENT '內容修改者(UUID)',
    IsLocked BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否被鎖定',
    LockedBy BINARY(16) DEFAULT NULL COMMENT '鎖定者(UUID)',
    LockedAt TIMESTAMP(6) DEFAULT NULL COMMENT '鎖定時間',
    version INT DEFAULT 1
) COMMENT '組織資產內容資料表';

-- 在所有表創建完成後加入外鍵約束
-- 保護組織不會因為擁有者被刪除而消失，同時允許組織解散後讓用戶保持獨立狀態(NULL)
ALTER TABLE Users
ADD CONSTRAINT fk_user_organization
FOREIGN KEY (OrganizationID) REFERENCES Organizations(OrganizationID) ON DELETE SET NULL;

-- Users 表索引優化
ALTER TABLE Users ADD INDEX idx_user_name (UserName); --登入使用 UserName
ALTER TABLE Users ADD INDEX idx_password_security (AccountStatus, PasswordChangedAt); -- 密碼安全相關查詢

-- OrganizationMembers 表索引優化
ALTER TABLE OrganizationMembers ADD INDEX idx_membership_time (OrganizationID, CreatedAt);

-- OrganizationAssets 表索引優化
DROP INDEX idx_createdat_desc ON OrganizationAssets; -- 移除可能重複的索引
ALTER TABLE OrganizationAssets ADD INDEX idx_active_assets (OrganizationID, IsDeleted, Status); -- 優化活躍資產查詢

-- ReportContentBlocks 表索引優化
ALTER TABLE ReportContentBlocks 
ADD INDEX idx_lock_status (IsLocked, LockedBy, LockedAt); -- 鎖定狀態查詢
DROP INDEX idx_content_state ON ReportContentBlocks; -- 簡化現有索引，去掉較少使用的LastModified
ALTER TABLE ReportContentBlocks ADD INDEX idx_content_state (status, IsLocked); -- 簡化現有索引，去掉較少使用的LastModified

-- Roles 表索引優化
ALTER TABLE Roles ADD INDEX idx_org_management (OrganizationID, RoleName, CreatedAt);

-- UserRoles 表索引優化
ALTER TABLE UserRoles ADD INDEX idx_role_assignment (OrganizationID, RoleID, CreatedAt);

-- RolePermissionMappings 表索引
ALTER TABLE RolePermissionMappings ADD INDEX idx_resource_action (ResourceType, ActionType);

-- Organizations 表索引優化
ALTER TABLE Organizations 
ADD INDEX idx_org_code (OrganizationCode); -- 加入代碼查詢優化
ADD INDEX idx_active_orgs (IsDeleted, OrganizationName); -- 活躍組織查詢

-- OrganizationAssets 軟刪除索引優化
ALTER TABLE OrganizationAssets ADD INDEX idx_deleted_status (IsDeleted, DeletedAt);