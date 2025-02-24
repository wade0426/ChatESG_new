export const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://api.yourcompany.com'  // 生產環境
  : 'http://localhost:8000'        // 開發環境

export const API_BASE_URL2 = process.env.NODE_ENV === 'production' 
  ? 'https://api.yourcompany.com'  // 生產環境
  : 'http://localhost:8002'        // 開發環境