-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- 主機： 127.0.0.1
-- 產生時間： 2025-01-30 11:08:20
-- 伺服器版本： 10.4.32-MariaDB
-- PHP 版本： 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- 資料庫： `chatesg_new`
--

-- --------------------------------------------------------

--
-- 資料表結構 `organizationmembers`
--

CREATE TABLE `organizationmembers` (
  `OrganizationMemberID` int(11) NOT NULL COMMENT '組織成員關係唯一標識',
  `OrganizationID` varchar(36) NOT NULL COMMENT '組織ID',
  `UserID` varchar(36) NOT NULL COMMENT '使用者ID',
  `Permission` enum('admin','member') NOT NULL DEFAULT 'member' COMMENT '使用者在組織中的權限',
  `Role` varchar(500) DEFAULT NULL COMMENT '使用者在組織中的角色',
  `CreatedAt` timestamp NOT NULL DEFAULT current_timestamp() COMMENT '加入時間'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='組織成員資料表';

--
-- 傾印資料表的資料 `organizationmembers`
--

INSERT INTO `organizationmembers` (`OrganizationMemberID`, `OrganizationID`, `UserID`, `Permission`, `Role`, `CreatedAt`) VALUES
(6, '8695f3b7-ae1b-43a9-a597-3ed7e9230354', 'e42a3bae-3705-4729-bcfe-3a4fa3d23cfc', 'admin', '[\"\\u4e00\\u822c\", \"\\u8cc7\\u8a0a\\u90e8\"]', '2025-01-02 12:33:51');

-- --------------------------------------------------------

--
-- 資料表結構 `organizations`
--

CREATE TABLE `organizations` (
  `OrganizationID` varchar(36) NOT NULL COMMENT '組織唯一標識 (UUID)',
  `OrganizationName` varchar(100) NOT NULL COMMENT '組織名稱',
  `OrganizationCode` varchar(8) NOT NULL COMMENT '組織加入代碼（8位大小寫字母和數字）',
  `OrganizationDescription` varchar(255) DEFAULT NULL COMMENT '組織描述',
  `AvatarUrl` varchar(255) DEFAULT NULL COMMENT '組織標誌URL',
  `OwnerID` varchar(36) NOT NULL COMMENT '組織擁有者ID',
  `ReportCount` int(11) DEFAULT 0 COMMENT '組織報告書數量',
  `RoleInfo` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '組織身份組資訊' CHECK (json_valid(`RoleInfo`)),
  `CreatedAt` timestamp NOT NULL DEFAULT current_timestamp() COMMENT '創建時間',
  `UpdatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '最後更新時間'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='組織資料表';

--
-- 傾印資料表的資料 `organizations`
--

INSERT INTO `organizations` (`OrganizationID`, `OrganizationName`, `OrganizationCode`, `OrganizationDescription`, `AvatarUrl`, `OwnerID`, `ReportCount`, `RoleInfo`, `CreatedAt`, `UpdatedAt`) VALUES
('8695f3b7-ae1b-43a9-a597-3ed7e9230354', 'o1', 'FCE58FBA', 'o1', 'https://raw.githubusercontent.com/wade0426/ChatESG_new/refs/heads/main/userPhoto/organization.png', 'e42a3bae-3705-4729-bcfe-3a4fa3d23cfc', 0, '{\"number_of_organization_roles\": 3, \"organization_roles\": [\"\\u4e00\\u822c\", \"\\u8cc7\\u8a0a\\u90e8\", \"\\u884c\\u92b7\\u90e8\"]}', '2025-01-02 12:33:51', '2025-01-02 12:33:51');

-- --------------------------------------------------------

--
-- 資料表結構 `users`
--

CREATE TABLE `users` (
  `UserID` varchar(36) NOT NULL COMMENT '使用者唯一標識 (UUID)',
  `UserName` varchar(100) NOT NULL COMMENT '使用者名稱',
  `UserPassword` varchar(255) NOT NULL COMMENT '使用者密碼（使用 bcrypt 或 Argon2 加密）',
  `UserEmail` varchar(100) NOT NULL COMMENT '使用者電子郵件（用於登錄和通知）',
  `AvatarUrl` varchar(255) DEFAULT NULL COMMENT '使用者頭像URL',
  `OrganizationID` varchar(36) DEFAULT NULL COMMENT '使用者所屬組織ID',
  `CreatedAt` timestamp NOT NULL DEFAULT current_timestamp() COMMENT '創建時間',
  `UpdatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '最後更新時間'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='使用者基本資料表';

--
-- 傾印資料表的資料 `users`
--

INSERT INTO `users` (`UserID`, `UserName`, `UserPassword`, `UserEmail`, `AvatarUrl`, `OrganizationID`, `CreatedAt`, `UpdatedAt`) VALUES
('e42a3bae-3705-4729-bcfe-3a4fa3d23cfc', 'n1', '$2b$12$nohh3K.eEJYQ9XPCx0.0AuxWpIJtb0EmuTlNOFtxdLUtNuxhrnmnS', 'laix678@gmail.com', 'https://raw.githubusercontent.com/wade0426/ChatESG_new/refs/heads/main/userPhoto/user-icons.png', '8695f3b7-ae1b-43a9-a597-3ed7e9230354', '2025-01-02 09:49:06', '2025-01-02 12:33:51'),
('f22ad4c4-fe50-4da6-9599-071234e1dd14', 'n2', '$2b$12$5XS3SD.kFW4/ThzpxTGC9.qLDsJRwOr1XgOePmMXVWYLiCbJ9zfw.', 'laix@gmai.com', 'https://raw.githubusercontent.com/wade0426/ChatESG_new/refs/heads/main/userPhoto/user-icons.png', NULL, '2025-01-02 12:22:31', '2025-01-02 12:22:31');

--
-- 已傾印資料表的索引
--

--
-- 資料表索引 `organizationmembers`
--
ALTER TABLE `organizationmembers`
  ADD PRIMARY KEY (`OrganizationMemberID`),
  ADD UNIQUE KEY `unique_member_organization` (`OrganizationID`,`UserID`),
  ADD KEY `UserID` (`UserID`);

--
-- 資料表索引 `organizations`
--
ALTER TABLE `organizations`
  ADD PRIMARY KEY (`OrganizationID`),
  ADD UNIQUE KEY `OrganizationCode` (`OrganizationCode`),
  ADD KEY `OwnerID` (`OwnerID`);

--
-- 資料表索引 `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`UserID`),
  ADD UNIQUE KEY `UserEmail` (`UserEmail`),
  ADD KEY `OrganizationID` (`OrganizationID`);

--
-- 在傾印的資料表使用自動遞增(AUTO_INCREMENT)
--

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `organizationmembers`
--
ALTER TABLE `organizationmembers`
  MODIFY `OrganizationMemberID` int(11) NOT NULL AUTO_INCREMENT COMMENT '組織成員關係唯一標識', AUTO_INCREMENT=7;

--
-- 已傾印資料表的限制式
--

--
-- 資料表的限制式 `organizationmembers`
--
ALTER TABLE `organizationmembers`
  ADD CONSTRAINT `organizationmembers_ibfk_1` FOREIGN KEY (`OrganizationID`) REFERENCES `organizations` (`OrganizationID`) ON DELETE CASCADE,
  ADD CONSTRAINT `organizationmembers_ibfk_2` FOREIGN KEY (`UserID`) REFERENCES `users` (`UserID`) ON DELETE CASCADE;

--
-- 資料表的限制式 `organizations`
--
ALTER TABLE `organizations`
  ADD CONSTRAINT `organizations_ibfk_1` FOREIGN KEY (`OwnerID`) REFERENCES `users` (`UserID`) ON DELETE CASCADE;

--
-- 資料表的限制式 `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`OrganizationID`) REFERENCES `organizations` (`OrganizationID`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
