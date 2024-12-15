# 資料庫設計

## 資料庫名稱
`chatesg`

## 資料表設計

### 使用者資料表
- **UserID** (使用者ID) [PK]
- **UserName** (使用者名稱)
- **UserPassword** (使用者密碼)
- **UserEmail** (使用者電子郵件)
- **UserOrganization** (參與的組織頻道)

### 組織頻道資料表
- **OrganizationID** (組織頻道ID) [PK]
- **OrganizationName** (組織頻道名稱)
- **OrganizationUser** (組織頻道人員) [JSON]  
  e.g. `{"使用者ID": {"身份組": "edit"}}`
- **OrganizationReport** (組織頻道的報告書) [直接給報告書ID]  
  e.g. `[1,2,3]`
- **CriteriaTemplates** (組織頻道的準則模板) [直接給準則模板ID]  
  e.g. `[1,2,3]`
- **OrganizationCompanyDataID** (組織頻道所屬公司資料) [直接給公司資料ID]  
  e.g. `[1,2,3]`

### 公司基本資料表
- **CompanyDataID** (公司資料ID) [PK]
- **CompanyDataName** (公司資料名稱)
- **CompanyDataContent** (公司資料內容) [JSON] 
 e.g. {"章節1":{"前言":"","長官的話":""},"章節2":{"前言":"","長官的話":""}}

### 準則模板表
- **CriteriaTemplateID** (準則模板ID) [PK]
- **CriteriaTemplateName** (準則模板名稱)
- **CriteriaTemplateContent** (準則模板內容) [JSON]

### 報告書資料表
- **ReportID** (報告書ID) [PK]
- **ReportName** (報告書名稱)
- **CompanyDataID** (公司資料ID)
- **ReportContent** (報告書內容) [JSON]
- **ReportSetting** (報告書設定檔) [JSON] [JSON要設定章節是否是唯讀]
- **ReportTemplate** (準則模板) [直接給準則模板ID]
- **ReportStatus** (報告書狀態)  
  e.g. "Draft(草稿)", "Audit(審核中)", "Finish(完成)"

### 報告書歷史資料表
- **HistoryID** (歷史記錄ID) [PK]
- **ReportID** (報告書ID) [FK]
- **EditedBy** (編輯者ID)
- **EditTimestamp** (編輯時間)
- **EditContent** (編輯內容) [JSON]
- **EditType** (編輯類型)  
  e.g. "Add(新增)", "Edit(修改)", "Delete(刪除)"