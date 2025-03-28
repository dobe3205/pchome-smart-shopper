from fastapi import FastAPI, Body,Depends,HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from contextlib import asynccontextmanager  # 用於建立 lifespan 上下文管理器
import logging

from sqlmodel import SQLModel,Field,create_engine,Session,select
from pydantic import BaseModel

from jose import JWTError, jwt  # JWT處理
from passlib.context import CryptContext  # 加密用

from package import rag #RAG
from datetime import datetime,timedelta
from typing import Annotated
import json
import os
from dotenv import load_dotenv
import jose


# 載入 .env 資料
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# 取得API key
gemini_api_key = os.getenv("gemini_api_key")
google_search_api_key = os.getenv("google_search_api_key")
google_cse_id = os.getenv("google_cse_id")
model_name = os.getenv("model_name")


# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#設定資料庫
databas_name="database.db"
database_path=f"sqlite:///{databas_name}"
connect_args={"check_same_thread":False}
engine=create_engine(database_path,connect_args=connect_args)

#用戶資料
class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)             
    user_name: str = Field(index=True, unique=True)             
    email: str = Field(index=True, unique=True, nullable=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: datetime = Field(nullable=True)
#問答紀錄
class QueryRecord(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    query: str
    response: str
    created_at: datetime = Field(default_factory=datetime.now)

def creat_db():
    SQLModel.metadata.create_all(engine)

#安全建立資料庫連接

async def creat_session():
    with Session(engine) as session:
        yield session

v_session=Annotated[Session,Depends(creat_session)]

#開serve初始化DB
@asynccontextmanager
async def lifespan(app:FastAPI):
    creat_db()
    print("資料庫建立完成")
    yield

#安全性設定
#加密方法
pw_content=CryptContext(schemes="bcrypt",deprecated="auto") 

#密碼加密
def hash_password(password:str)->str:
    return  pw_content.hash(password)

#驗證密碼正確
def verfiy_password(plain_password:str,hash_password:str):
    return pw_content.verify(plain_password,hash_password)

#驗證使用者登入
def verfiy_user(session:v_session,user_name:str,password:str):
    user=session.exec(select(User).where(User.user_name==user_name))
    if not user or not verfiy_password(password,user.hashed_password):
        return None
    return user
    


    
app = FastAPI(
    title="商品比較RAG系統",
    description="基於RAG的商品比較系統",
    lifespan=lifespan
)


#CORS
origins = [
    "http://localhost:4200",
    "http://localhost:8000"
]
app.add_middleware(
    CORSMiddleware, #CORS
    allow_origins=origins,  #允許的url
    allow_credentials=True, #憑證
    allow_methods=["*"],    #允許所有method(GET、POST...)
    allow_headers=["*"],    #允許所有header
)


@app.post("/api/response")
async def response(body=Body(None)):
    """
    處理用戶產品比較請求
    """
    try:
        # 處理 request body
        if isinstance(body, dict):
            user_query = body["content"]
        else:
            # 如果不是字典，嘗試解析 JSON
            user_query = json.loads(body)["content"]
        logger.info(f"收到用戶查詢: {user_query}")
        
        # step1: LLM生成搜尋關鍵詞
        logger.info("step1: LLM生成搜尋關鍵詞")
        keywords_prompt = rag.create_search_keywords_prompt(user_query) #得到關鍵字
        search_keywords = rag.gemini_response(keywords_prompt, gemini_api_key, model_name)
        logger.info(f"生成的搜尋關鍵詞: {search_keywords}")
        
        # step2: 執行google搜尋取得產品資訊
        logger.info("step2: 執行google搜尋取得產品資訊")
        search_results = rag.google_search(search_keywords, google_search_api_key, google_cse_id, num_results=10)
        
        # step3: step3: 整理pchome產品資訊
        logger.info("step3: 整理pchome產品資訊")
        retrival_info = rag.pchome_search(search_results)
        
        # step4: 生成產品比較和分析
        logger.info("step4: 生成產品比較和分析")
        final_prompt = rag.final_comparison_prompt(user_query,retrival_info)
        final_response = rag.gemini_response(final_prompt, gemini_api_key, model_name)
        
        response = extract_json_from_response(final_response)
        return JSONResponse(response)
        
    except Exception as e:
        logger.error(f"處理請求時發生錯誤: {str(e)}")
        error_response = {"error": f"處理請求時發生錯誤: {str(e)}"}
        return JSONResponse(content=error_response, status_code=500)

#處理Gemini回應markdown
def extract_json_from_response(response):
    if "```json" in response:
        parts = response.split("```json")
        json_part = parts[1].split("```")[0].strip()
        return json_part


# 靜態文件
app.mount("/", StaticFiles(directory="static", html=True), name="static")