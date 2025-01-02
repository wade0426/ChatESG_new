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
    UserID VARCHAR(36) PRIMARY KEY COMMENT '使用者唯一標識 (UUID)',
    UserName VARCHAR(100) NOT NULL COMMENT '使用者名稱',
    UserPassword VARCHAR(255) NOT NULL COMMENT '使用者密碼（使用 bcrypt 或 Argon2 加密）',
    UserEmail VARCHAR(100) NOT NULL UNIQUE COMMENT '使用者電子郵件（用於登錄和通知）',
    -- avatarUrl
    AvatarUrl VARCHAR(255) COMMENT '使用者頭像URL',
    -- organization
    OrganizationID VARCHAR(36) COMMENT '使用者所屬組織ID',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最後更新時間',
    FOREIGN KEY (OrganizationID) REFERENCES Organizations(OrganizationID) ON DELETE SET NULL
) COMMENT '使用者基本資料表';

-- --------------------------------------------------------
-- 組織資料表
-- 用於管理不同的組織及其基本信息
-- --------------------------------------------------------
CREATE TABLE Organizations (
    OrganizationID VARCHAR(36) PRIMARY KEY COMMENT '組織唯一標識 (UUID)',
    OrganizationName VARCHAR(100) NOT NULL COMMENT '組織名稱',
    OrganizationCode VARCHAR(8) NOT NULL UNIQUE COMMENT '組織加入代碼（8位大小寫字母和數字）',
    OrganizationDescription VARCHAR(255) COMMENT '組織描述',
    AvatarUrl VARCHAR(255) COMMENT '組織標誌URL',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最後更新時間'
) COMMENT '組織資料表';

-- --------------------------------------------------------
-- 組織成員資料表（多對多關聯，包含身份組）
-- 用於管理組織與成員之間的關係以及成員在組織內的身份組
-- --------------------------------------------------------
CREATE TABLE OrganizationMembers (
    OrganizationMemberID VARCHAR(36) PRIMARY KEY COMMENT '組織成員關係唯一標識 (UUID)',
    OrganizationID VARCHAR(36) NOT NULL COMMENT '組織ID',
    UserID VARCHAR(36) NOT NULL COMMENT '使用者ID',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '加入時間',
    FOREIGN KEY (OrganizationID) REFERENCES Organizations(OrganizationID) ON DELETE CASCADE,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    UNIQUE KEY unique_member_organization (OrganizationID, UserID) -- 確保同一使用者在同一組織中只有一條記錄
) COMMENT '組織成員資料表';

-- --------------------------------------------------------
-- 身份組資料表
-- 用於定義組織內的身份組及其權限
-- --------------------------------------------------------
CREATE TABLE Roles (
    RoleID VARCHAR(36) PRIMARY KEY COMMENT '身份組唯一標識 (UUID)',
    OrganizationID VARCHAR(36) NOT NULL COMMENT '組織ID',
    RoleName VARCHAR(100) NOT NULL COMMENT '身份組名稱',
    Permissions JSON COMMENT '身份組權限設置 (JSON格式)',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最後更新時間',
    FOREIGN KEY (OrganizationID) REFERENCES Organizations(OrganizationID) ON DELETE CASCADE
) COMMENT '身份組資料表';

-- --------------------------------------------------------
-- 組織成員身份組關聯表（多對多關聯）
-- 用於管理成員擁有的多個身份組
-- --------------------------------------------------------
CREATE TABLE UserRoles (
    UserRoleID VARCHAR(36) PRIMARY KEY COMMENT '使用者身份組關係唯一標識 (UUID)',
    OrganizationMemberID VARCHAR(36) NOT NULL COMMENT '組織成員關係ID',
    RoleID VARCHAR(36) NOT NULL COMMENT '身份組ID',
    FOREIGN KEY (OrganizationMemberID) REFERENCES OrganizationMembers(OrganizationMemberID) ON DELETE CASCADE,
    FOREIGN KEY (RoleID) REFERENCES Roles(RoleID) ON DELETE CASCADE,
    UNIQUE KEY unique_user_role_in_organization (OrganizationMemberID, RoleID) -- 確保同一成員在同一組織中不會被分配相同的身份組多次
) COMMENT '組織成員身份組關聯表';

-- --------------------------------------------------------
-- 操作日誌資料表
-- 用於記錄系統的關鍵操作，方便稽核
-- --------------------------------------------------------
CREATE TABLE AuditLogs (
    LogID VARCHAR(36) PRIMARY KEY COMMENT '日誌唯一標識 (UUID)',
    OrganizationID VARCHAR(36) COMMENT '組織ID（如果適用）',
    UserID VARCHAR(36) COMMENT '執行操作的使用者ID',
    Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '操作時間',
    Action VARCHAR(255) NOT NULL COMMENT '操作類型',
    Details TEXT COMMENT '操作詳細信息',
    FOREIGN KEY (OrganizationID) REFERENCES Organizations(OrganizationID) ON DELETE SET NULL,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE SET NULL
) COMMENT '操作日誌資料表';

-- --------------------------------------------------------
-- 公司基本資料表
-- 存儲公司相關的基本信息
-- --------------------------------------------------------
CREATE TABLE CompanyData (
    CompanyDataID VARCHAR(36) PRIMARY KEY COMMENT '公司資料唯一標識 (UUID)',
    OrganizationID VARCHAR(36) NOT NULL COMMENT '所屬組織ID',
    CompanyDataName VARCHAR(100) NOT NULL COMMENT '公司資料名稱',
    DataContent JSON COMMENT '公司資料內容，包含各章節的詳細信息 (可根據實際需求調整結構)',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最後更新時間',
    FOREIGN KEY (OrganizationID) REFERENCES Organizations(OrganizationID) ON DELETE CASCADE
) COMMENT '公司基本資料表';

-- --------------------------------------------------------
-- 準則模板表
-- 用於存儲 ESG 報告的各種準則模板
-- --------------------------------------------------------
CREATE TABLE CriteriaTemplates (
    CriteriaTemplateID VARCHAR(36) PRIMARY KEY COMMENT '準則模板唯一標識 (UUID)',
    TemplateName VARCHAR(100) NOT NULL COMMENT '準則模板名稱',
    TemplateContent JSON COMMENT '準則模板的具體內容和結構',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最後更新時間'
) COMMENT '準則模板資料表';

-- --------------------------------------------------------
-- 報告書資料表
-- 存儲 ESG 報告的主要信息
-- --------------------------------------------------------
CREATE TABLE Reports (
    ReportID VARCHAR(36) PRIMARY KEY COMMENT '報告書唯一標識 (UUID)',
    OrganizationID VARCHAR(36) NOT NULL COMMENT '所屬組織ID',
    ReportName VARCHAR(255) NOT NULL COMMENT '報告書名稱',
    CompanyDataID VARCHAR(36) COMMENT '關聯的公司資料ID',
    CriteriaTemplateID VARCHAR(36) COMMENT '使用的準則模板ID',
    Status ENUM('Draft', 'PendingReview', 'Approved', 'Published') DEFAULT 'Draft' COMMENT '報告狀態：草稿/待審核/已批准/已發布',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最後更新時間',
    FOREIGN KEY (OrganizationID) REFERENCES Organizations(OrganizationID) ON DELETE CASCADE,
    FOREIGN KEY (CompanyDataID) REFERENCES CompanyData(CompanyDataID) ON DELETE SET NULL,
    FOREIGN KEY (CriteriaTemplateID) REFERENCES CriteriaTemplates(CriteriaTemplateID) ON DELETE SET NULL
) COMMENT '報告書資料表';

-- --------------------------------------------------------
-- 報告書章節資料表
-- 用於存儲報告書的結構化內容，支持多層級
-- --------------------------------------------------------
CREATE TABLE ReportSections (
    SectionID VARCHAR(36) PRIMARY KEY COMMENT '章節唯一標識 (UUID)',
    ReportID VARCHAR(36) NOT NULL COMMENT '所屬報告書ID',
    ParentSectionID VARCHAR(36) COMMENT '父章節ID，用於建立層級結構',
    Title VARCHAR(255) NOT NULL COMMENT '章節標題',
    Content LONGTEXT COMMENT '章節內容 (富文本格式)',
    SectionOrder INT UNSIGNED COMMENT '章節順序',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最後更新時間',
    FOREIGN KEY (ReportID) REFERENCES Reports(ReportID) ON DELETE CASCADE,
    FOREIGN KEY (ParentSectionID) REFERENCES ReportSections(SectionID) ON DELETE CASCADE
) COMMENT '報告書章節資料表';

-- --------------------------------------------------------
-- 報告書歷史資料表
-- 用於追踪報告書的修改歷史
-- --------------------------------------------------------
CREATE TABLE ReportHistory (
    HistoryID VARCHAR(36) PRIMARY KEY COMMENT '歷史記錄唯一標識 (UUID)',
    ReportID VARCHAR(36) NOT NULL COMMENT '關聯的報告書ID',
    SectionID VARCHAR(36) COMMENT '關聯的章節ID (如果適用)',
    EditedBy VARCHAR(36) COMMENT '編輯者的使用者ID',
    EditTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '編輯時間',
    EditType ENUM('Create', 'Update', 'Delete') COMMENT '編輯類型：創建/更新/刪除',
    OldContent LONGTEXT COMMENT '舊的內容 (適用於更新)',
    NewContent LONGTEXT COMMENT '新的內容 (適用於創建/更新)',
    FOREIGN KEY (ReportID) REFERENCES Reports(ReportID) ON DELETE CASCADE,
    FOREIGN KEY (SectionID) REFERENCES ReportSections(SectionID) ON DELETE SET NULL,
    FOREIGN KEY (EditedBy) REFERENCES Users(UserID) ON DELETE SET NULL
) COMMENT '報告書歷史記錄表';

-- --------------------------------------------------------
-- 報告書設定資料表
-- 存儲報告書的相關設定，例如發布狀態和分享設定
-- --------------------------------------------------------
CREATE TABLE ReportSettings (
    ReportSettingID VARCHAR(36) PRIMARY KEY COMMENT '報告書設定唯一標識 (UUID)',
    ReportID VARCHAR(36) NOT NULL UNIQUE COMMENT '關聯的報告書ID',
    IsPublished BOOLEAN DEFAULT FALSE COMMENT '是否已發布',
    PublishAccess ENUM('Public', 'Organization') DEFAULT 'Organization' COMMENT '發布訪問權限',
    FOREIGN KEY (ReportID) REFERENCES Reports(ReportID) ON DELETE CASCADE
) COMMENT '報告書設定資料表';

-- --------------------------------------------------------
-- 報告書章節權限資料表
-- 用於設定不同身份組對報告書章節的權限
-- --------------------------------------------------------
CREATE TABLE ReportSectionPermissions (
    PermissionID VARCHAR(36) PRIMARY KEY COMMENT '權限唯一標識 (UUID)',
    SectionID VARCHAR(36) NOT NULL COMMENT '章節ID',
    RoleID VARCHAR(36) NOT NULL COMMENT '身份組ID',
    PermissionType ENUM('View', 'Edit', 'Review') NOT NULL COMMENT '權限類型',
    FOREIGN KEY (SectionID) REFERENCES ReportSections(SectionID) ON DELETE CASCADE,
    FOREIGN KEY (RoleID) REFERENCES Roles(RoleID) ON DELETE CASCADE,
    UNIQUE KEY unique_section_role_permission (SectionID, RoleID, PermissionType)
) COMMENT '報告書章節權限資料表';

-- --------------------------------------------------------
-- 報告書章節評論資料表
-- 用於存儲對報告書特定章節的評論
-- --------------------------------------------------------
CREATE TABLE ReportSectionComments (
    CommentID VARCHAR(36) PRIMARY KEY COMMENT '評論唯一標識 (UUID)',
    SectionID VARCHAR(36) NOT NULL COMMENT '章節ID',
    UserID VARCHAR(36) NOT NULL COMMENT '評論者使用者ID',
    Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '評論時間',
    CommentText TEXT NOT NULL COMMENT '評論內容',
    FOREIGN KEY (SectionID) REFERENCES ReportSections(SectionID) ON DELETE CASCADE,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
) COMMENT '報告書章節評論資料表';

-- --------------------------------------------------------
-- 準則關聯性說明資料表 (可選，如果需要更精細的管理)
-- --------------------------------------------------------
CREATE TABLE CriteriaRelationships (
    RelationshipID VARCHAR(36) PRIMARY KEY COMMENT '關聯唯一標識 (UUID)',
    CriteriaTemplateID VARCHAR(36) NOT NULL COMMENT '準則模板ID',
    RelatedCriteriaTemplateID VARCHAR(36) NOT NULL COMMENT '相關準則模板ID',
    Description TEXT COMMENT '關聯性說明',
    FOREIGN KEY (CriteriaTemplateID) REFERENCES CriteriaTemplates(CriteriaTemplateID) ON DELETE CASCADE,
    FOREIGN KEY (RelatedCriteriaTemplateID) REFERENCES CriteriaTemplates(CriteriaTemplateID) ON DELETE CASCADE
) COMMENT '準則關聯性說明資料表';

-- --------------------------------------------------------
-- 索引 (提升查詢效能)
-- --------------------------------------------------------
CREATE INDEX idx_report_organization ON Reports(OrganizationID);
CREATE INDEX idx_report_status ON Reports(Status);
CREATE INDEX idx_report_company_data ON Reports(CompanyDataID);
CREATE INDEX idx_report_criteria_template ON Reports(CriteriaTemplateID);
CREATE INDEX idx_report_section_report ON ReportSections(ReportID);
CREATE INDEX idx_report_section_parent ON ReportSections(ParentSectionID);
CREATE INDEX idx_report_history_report ON ReportHistory(ReportID);
CREATE INDEX idx_report_history_user ON ReportHistory(EditedBy);
CREATE INDEX idx_organization_owner ON Organizations(OwnerID);
CREATE INDEX idx_organization_members_org ON OrganizationMembers(OrganizationID);
CREATE INDEX idx_organization_members_user ON OrganizationMembers(UserID);
CREATE INDEX idx_user_roles_member ON UserRoles(OrganizationMemberID);
CREATE INDEX idx_user_roles_role ON UserRoles(RoleID);
CREATE INDEX idx_audit_logs_org ON AuditLogs(OrganizationID);
CREATE INDEX idx_audit_logs_user ON AuditLogs(UserID);
CREATE INDEX idx_report_section_permissions_section ON ReportSectionPermissions(SectionID);
CREATE INDEX idx_report_section_permissions_role ON ReportSectionPermissions(RoleID);
CREATE INDEX idx_report_section_comments_section ON ReportSectionComments(SectionID);
CREATE INDEX idx_report_section_comments_user ON ReportSectionComments(UserID);

-- --------------------------------------------------------
-- 注意事項：
-- 1. 所有 VARCHAR 欄位的長度可根據實際需求調整。
-- 2. 使用 UUID 作為主鍵，確保全局唯一性。
-- 3. 密碼存儲應使用強加密算法（如 bcrypt 或 Argon2）。
-- 4. JSON 欄位的具體結構應在應用層面進行驗證和處理。
-- 5. 時間戳欄位使用 `TIMESTAMP`，並設置默認值和更新時自動更新。
-- 6. 根據實際查詢需求，可以進一步優化索引。
-- 7. 某些表的命名可能可以根據團隊習慣進行調整，例如 `Roles` 可以考慮命名為 `IdentityGroups`。
-- 8. 準則關聯性說明資料表 `CriteriaRelationships` 是可選的，如果需要在資料庫層面管理準則之間的關係，則可以添加。
-- --------------------------------------------------------