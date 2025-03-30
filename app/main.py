from fastapi import FastAPI, Body,Depends,HTTPException,status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from contextlib import asynccontextmanager  # 用於建立 lifespan 
import logging

from sqlmodel import SQLModel,Field,create_engine,Session,select
from pydantic import BaseModel

from jose import JWTError, jwt  # JWT處理
from passlib.context import CryptContext  # 加密用

from package import rag #RAG
from datetime import datetime,timedelta
from typing import Annotated,Optional,Dict
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

#設定JWT參數
SECRET_KEY=os.getenv("secret_key")
ALGORITHM = "HS256"  # 常用方法 HS256, HS384, HS512, RS256
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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
pw_content=CryptContext(schemes=["bcrypt"],deprecated="auto") 

#密碼加密
def hash_password(password:str)->str:
    return  pw_content.hash(password)

#驗證密碼正確
def verfiy_password(plain_password:str,hash_password:str):
    return pw_content.verify(plain_password,hash_password)

#驗證使用者登入
def verfiy_user(session:v_session,user_name:str,password:str):
    user=session.exec(select(User).where(User.user_name==user_name)).first()
    if not user or not verfiy_password(password,user.hashed_password):
        return None
    return user
    
#產生JWT
def create_access_token(user_id: int, user_name: str, expires_delta: Optional[timedelta] = None):
    """
    建立JWT
    
    Args:
        user_id:用戶ID
        user_name:用戶名稱
        expires_delta:過期時間
        
    Returns:
        JWT
    """
    # 建立payload資料
    payload = {
        "sub": user_name,  # subject (主題) - 標識用戶的唯一值
        "id": user_id,     # 用戶ID，方便後續查詢
        "type": "access_token",  # token類型
        "iat": datetime.now(),  # issued at (簽發時間)
    }
    
    # 設置過期時間
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload.update({"exp": expire})  # expiration time (過期時間)
    
    # 生成JWT
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

#回應模型
class UserResponse(BaseModel):
    id: int
    user_name: str
    email: str
    is_active: bool
    created_at: datetime

# 問答形式回應模型
class QueryRecordResponse(BaseModel):
    id: int
    user_id: int
    query: str
    response: str
    created_at: datetime

# 多筆問答記錄回應模型
class QueryHistoryResponse(BaseModel):
    records: list[QueryRecordResponse]
    total: int

#給前端用
class token(BaseModel):
    access_token:str
    token_type:str

#驗證用戶用
class TokenData(BaseModel):
    username: Optional[str] = None

#處理Gemini回應markdown
def extract_json_from_response(response):
    if "```json" in response:
        parts = response.split("```json")
        json_part = parts[1].split("```")[0].strip()
        return json_part

#OAuth2 token
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/api/token")

app = FastAPI(
    title="商品比較RAG系統",
    description="基於RAG的商品比較系統",
    lifespan=lifespan
)


#CORS
origins = [
    "http://localhost:4200"
]
app.add_middleware(
    CORSMiddleware, #CORS
    allow_origins=origins,  #允許的url
    allow_credentials=True, #憑證
    allow_methods=["*"],    #允許所有method(GET、POST...)
    allow_headers=["*"],    #允許所有header
)



# 用戶創建模型
class UserCreate(BaseModel):
    user_name: str
    email: str
    password: str



# 用戶註冊路由
@app.post("/api/register", response_model=UserResponse)
def register_user(user: UserCreate, session: v_session):
    """註冊新用戶"""
    # 檢查用戶名是否已存在
    statement = select(User).where(User.user_name == user.user_name)
    db_user = session.exec(statement).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用戶名已被使用")
    
    # 檢查email是否已存在
    statement = select(User).where(User.email == user.email)
    db_user = session.exec(statement).first()
    if db_user:
        raise HTTPException(status_code=400, detail="email已被使用")
    
    # 創建新用戶
    hashed_password = hash_password(user.password)
    db_user = User(
        user_name=user.user_name,
        email=user.email,
        hashed_password=hashed_password,
        created_at=datetime.now()
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

# 登入路由
@app.post("/api/token", response_model=token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],session:v_session):
    """登入並獲取token"""
    # 認證用戶
    user = verfiy_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶名或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 建立token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user_id=user.id, user_name=user.user_name, expires_delta=access_token_expires
    )
    
    # 回傳token
    return {"access_token": access_token, "token_type": "bearer"}

# 獲取當前用戶
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session:v_session):
    """從token獲取當前用戶"""
    #定義錯誤訊息
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認證失敗",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解碼token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # 獲取用戶資料
    statement = select(User).where(User.user_name == token_data.username)
    user = session.exec(statement).first()
    if user is None:
        raise credentials_exception
    return user

# 獲取當前活躍用戶
async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    """確認用戶是活躍的"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用戶已停用")
    return current_user

# 獲取當前用戶資料
@app.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    """獲取當前登入用戶資訊"""
    return current_user

# 獲取用戶的問答歷史記錄
@app.get("/api/history", response_model=QueryHistoryResponse)
async def get_user_history(
    skip: int = 0,
    limit: int = 10,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    session: v_session = None
):
    """獲取用戶的問答歷史記錄"""
    
    # 查詢用戶的所有問答記錄，按創建時間降序排列
    statement = select(QueryRecord).where(QueryRecord.user_id == current_user.id).order_by(QueryRecord.created_at.desc()).offset(skip).limit(limit)
    
    records = session.exec(statement).all()
    
    # 獲取總記錄數
    total_count = session.exec(select(QueryRecord).where(QueryRecord.user_id == current_user.id)).all()
    
    return {
        "records": records,
        "total": len(total_count)
    }

# 獲取最新的用戶問答
@app.get("/api/history/latest", response_model=QueryRecordResponse)
async def get_latest_record(
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    session: v_session = None
):
    """獲取用戶最新的問答記錄"""
    
    statement = select(QueryRecord).where(QueryRecord.user_id == current_user.id)\
        .order_by(QueryRecord.created_at.desc()).limit(1)
    
    record = session.exec(statement).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="無問答記錄")
    
    return record

# 根據ID獲取特定的問答記錄
@app.get("/api/history/{record_id}", response_model=QueryRecordResponse)
async def get_record_by_id(
    record_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    session: v_session = None
):
    """根據ID獲取特定的問答記錄"""
    
    # 查詢指定的記錄，並確保屬於當前用戶
    statement = select(QueryRecord).where(
        QueryRecord.id == record_id,
        QueryRecord.user_id == current_user.id
    )
    
    record = session.exec(statement).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="記錄不存在或無權存取")
    
    return record

# 刪除問答記錄
@app.delete("/api/history/{record_id}")
async def delete_record(
    record_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    session: v_session = None
):
    """刪除問答記錄"""
    
    # 查詢指定的記錄，並確保屬於當前用戶
    statement = select(QueryRecord).where(
        QueryRecord.id == record_id,
        QueryRecord.user_id == current_user.id
    )
    
    record = session.exec(statement).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="記錄不存在或無權存取")
    
    # 刪除記錄
    session.delete(record)
    session.commit()
    
    return {"message": "記錄刪除成功"}

@app.post("/api/response")
async def response(
    body=Body(None), 
    current_user: Annotated[User, Depends(get_current_active_user)] = None, 
    session: v_session = None
):
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
        search_results = rag.google_search(search_keywords, google_search_api_key, google_cse_id, num_results=20)
        
        # step3: step3: 整理pchome產品資訊
        logger.info("step3: 整理pchome產品資訊")
        retrival_info = rag.pchome_search(search_results)
        
        # step4: 生成產品比較和分析
        logger.info("step4: 生成產品比較和分析")
        final_prompt = rag.final_comparison_prompt(user_query,retrival_info)
        final_response = rag.gemini_response(final_prompt, gemini_api_key, model_name)
        
        # 解析回應
        response_json_str = extract_json_from_response(final_response)
        
        # 將字串解析為Python字典
        if response_json_str:
            response_json = json.loads(response_json_str)
        else:
            # 如果無法提取JSON，則使用完整回應
            response_json = {"response": final_response}
        
        # 儲存問答記錄
        query_record = QueryRecord(
            user_id=current_user.id,
            query=user_query,
            response=final_response
        )
        session.add(query_record)
        session.commit()
        session.refresh(query_record)
        
        return JSONResponse(content=response_json)
        
    except Exception as e:
        logger.error(f"處理請求時發生錯誤: {str(e)}")
        error_response = {"error": f"處理請求時發生錯誤: {str(e)}"}
        return JSONResponse(content=error_response, status_code=500)


# 靜態文件
#app.mount("/static", StaticFiles(directory="static"), name="static")