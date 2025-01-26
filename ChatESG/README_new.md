# ChatESG - 企業永續報告書協作平台

## 專案描述

ChatESG 是一個專門設計用於協助企業編寫和管理永續報告書(ESG Report)的網頁應用平台。該平台提供以下核心功能：

- 多人協作編輯報告書
- 組織管理與權限控制
- 即時註解與版本控制
- 客製化報告書模板
- 深色/淺色主題切換
- 響應式設計

## 技術架構

### 前端
- Vue 3 + Vite
- Pinia 狀態管理
- Vue Router 路由管理
- Material Design Icons
- CSS3 客製化樣式

### 後端
- FastAPI
- MySQL 資料庫
- JWT 認證
- bcrypt 密碼加密

## 安裝說明

1. 安裝相依套件：

```bash
# 前端
cd frontend
npm install

# 後端
cd API
pip install -r requirements.txt
```

2. 資料庫設定：


```34:41:API/chatESG_FastAPI.py
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',  # 請根據實際情況修改
    'password': '',  # 請根據實際情況修改
    'db': 'chatesg_new',
    'charset': 'utf8mb4'
}
```


3. 環境變數設定：
- 設定 JWT SECRET_KEY
- 設定資料庫連線參數
- 設定 CORS 允許的域名

## 使用方法

1. 啟動後端服務：

```bash
cd API
uvicorn chatESG_FastAPI:app --reload
```

2. 啟動前端開發伺服器：

```bash
cd frontend
npm run dev
```

3. 開啟瀏覽器訪問：`http://localhost:5173`

## 主要功能模組

### 1. 使用者認證
- 登入/登出
- 個人資料管理
- JWT token 驗證

### 2. 組織管理
- 創建/加入組織
- 成員角色管理
- 組織資料設定

### 3. 報告書編輯
- 多人即時協作
- 版本控制
- 註解功能
- 自動儲存

### 4. 介面設計
- 響應式布局
- 深色/淺色主題
- 側邊欄導航
- 使用者友善的編輯器

## 目錄結構

```
src/
├── assets/         # 靜態資源
├── components/     # Vue 元件
├── router/         # 路由配置
├── stores/         # Pinia 狀態管理
└── App.vue         # 根元件

API/
└── chatESG_FastAPI.py  # 後端 API
```

## 開發中功能

- 報告書範本管理
- 稽核日誌
- 進階搜尋功能
- 檔案匯出功能

## 注意事項

- 開發環境需要 Node.js 16+ 和 Python 3.8+
- 確保 MySQL 服務正常運行