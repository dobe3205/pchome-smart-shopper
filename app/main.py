from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from package import rag
from fastapi.staticfiles import StaticFiles
import json
import os
import logging
from dotenv import load_dotenv

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="商品比較RAG系統",
    description="基於RAG的商品比較系統",
    version="1.0.0"
)

# 載入 .env 檔案
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# 取得API key
gemini_api_key = os.getenv("gemini_api_key")
google_search_api_key = os.getenv("google_search_api_key")
google_cse_id = os.getenv("google_cse_id")
model_name = os.getenv("model_name")



@app.post("/respone")
async def respone(body=Body(None)):
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

def extract_json_from_response(response):
    if "```json" in response:
        parts = response.split("```json")
        json_part = parts[1].split("```")[0].strip()
        return json_part


# 靜態文件
app.mount("/", StaticFiles(directory="static", html=True), name="static")