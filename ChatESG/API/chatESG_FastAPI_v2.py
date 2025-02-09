# ChatESG_FastAPI_v2

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
import json
from contextlib import asynccontextmanager
import uuid
# 準則驗證
from rag_main import find_most_relevant_answer
from ESG_Criteria_Assessment import Gemini_ESG_Criteria_Assessment

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




# 準則檢驗
@app.post("/api/report/gri_verification_criteria_by_chapter")
async def gri_verification_criteria_by_chapter(data: dict):
    try:
        # 傳入整個大章節標題和內容
        esg_report = data.get("chapterTitle_text_content")

        if not all([esg_report]):
            raise HTTPException(status_code=400, detail="缺少必要參數")
    
        # 測試資料
        api_keys = ["AI"]
        model_name = "gemini-2.0-flash-lite-preview-02-05"
        config = {
            "n": 1,
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 1,
        }
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        max_retry = 1
        
        # 建立物件
        ESG_Criteria_Assessment = Gemini_ESG_Criteria_Assessment(api_keys, model_name, config, base_url, max_retry)

        # 取得對應 GRI 準則
        response = await ESG_Criteria_Assessment.generate_gri_criteria(esg_report)
        # print(response)
        choice = response.choices[0]
        message = choice.message
        content = message.content

        # 建立包含完整 GRI 準則描述的列表
        criteria_lst = []
        try:
            esg_criteria_json = json.loads(content)
            for indicator in esg_criteria_json['GRI_Indicators']:
                gri_text = f"{indicator['indicator']} {indicator['description']}"
                criteria_lst.append(gri_text)
        except json.JSONDecodeError as e:
            print(f"JSON 解析錯誤: {str(e)}")
            raise HTTPException(status_code=500, detail=f"GRI 準則解析失敗: {str(e)}")

        # 開檔 開啟已經涵蓋的準則
        file_path = r"D:\\NTCUST\\Project\\ChatESG_new\\ChatESG\\API\\rag_file\\GRI_準則.txt"
        with open(file_path, 'r', encoding='utf-8') as file:
            # 已經涵蓋的準則
            covered_standards_text = file.read()
        covered_standards_list = covered_standards_text.split('\n') #[GRI 1：基礎]
        covered_standards_list = [item.split('：')[0] for item in covered_standards_list] #[GRI 1]

        # 使用集合未涵蓋的準則
        uncovered_standards = set()
        # criteria_lst 是這篇報告書的 GRI 準則清單
        rag_content = ""
        for criteria in criteria_lst:
            # 將 criteria 轉換成 GRI 405
            # criteria = GRI 405-1 董事會性別多樣性
            # 使用空格分割字串，取前兩個部分
            gri_parts = criteria.split(' ')[:2] # [GRI, 405-1]
            # 組合成 GRI 405-1 格式
            gri_code = ' '.join(gri_parts) # GRI 405-1
            # 從 gri_code 中移除最後一個 -1 部分
            gri_code = gri_code.rsplit('-', 1)[0] # GRI 405

            # print(f"gri_code: {gri_code}")
            if gri_code in covered_standards_list:
                print(f"已經涵蓋的準則: {gri_code}")
                content, source, score = find_most_relevant_answer(criteria)
                rag_content+=f"{content}\n"
            else:
                uncovered_standards.add(gri_code)
        
        # 輸出未涵蓋的準則
        for gri_code in uncovered_standards:
            print(f"未涵蓋的準則: {gri_code}")

        # esg_report 是 章節名稱 + 章節內容
        # prompt_input_content 是 esg_report 加 rag_content
        prompt_input_content = f"{esg_report}\n\n\n###GRI 準則參考：{rag_content}###"
        # print(f"prompt_input_content: {prompt_input_content}")
        # 檢驗結果
        esg_criteria_verification_result = await ESG_Criteria_Assessment.gri_verification_criteria_by_chapter(prompt_input_content)

        # 將字串轉換為 JSON 物件
        choice = esg_criteria_verification_result.choices[0]
        message = choice.message
        content = message.content
        
        # API 返回的原始内容
        # print("API 返回的原始内容:")
        # print(content)
        
        try:
            verification_json = json.loads(content)
            return {"status": "success", "data": verification_json}
        except json.JSONDecodeError as e:
            print(f"JSON 解析錯誤: {str(e)}")
            print(f"錯誤位置的內容: {content[max(0, e.pos-50):min(len(content), e.pos+50)]}")
            raise HTTPException(
                status_code=500, 
                detail={
                    "error": "JSON 解析失敗",
                    "message": str(e),
                    "position": e.pos,
                    "line": e.lineno,
                    "column": e.colno,
                    "content_sample": content[:200] + "..." if len(content) > 200 else content
                }
            )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"錯誤詳情: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")



if __name__ == "__main__":
    uvicorn.run("chatESG_FastAPI_v2:app", host="0.0.0.0", port=8002, reload=True)