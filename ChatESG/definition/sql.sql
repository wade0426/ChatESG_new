-- 角色權限映射表
CREATE TABLE RolePermissionMappings (
    RoleID BINARY(16) NOT NULL COMMENT '角色(UUID)',
    PermissionChapterID BINARY(16) NOT NULL COMMENT '章節權限識別標籤(UUID)',
    ResourceType VARCHAR(50) DEFAULT 'report/template/company_info' COMMENT '資源類型',
    ActionType ENUM('read', 'read_write', 'no_access', 'create', 'update', 'delete') DEFAULT 'read' COMMENT '操作類型',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間',
    PRIMARY KEY (RoleID, PermissionChapterID),
    FOREIGN KEY (RoleID) REFERENCES Roles(RoleID) ON DELETE CASCADE
) COMMENT '角色權限映射表'; 