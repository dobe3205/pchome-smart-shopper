from fastapi import FastAPI,Body
from fastapi.responses import JSONResponse
from package import rag
from fastapi.staticfiles import StaticFiles
import json
import os
from dotenv import load_dotenv

app=FastAPI()

# 載入 .env 檔案
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)


#取得API key
gemini_api_key=os.getenv("gemini_api_key")
google_search_api_key=os.getenv("google_search_api_key")
google_cse_id =os.getenv("google_cse_id")
model_name=os.getenv("model_name")

@app.post("/respone")
async def respone(body=Body(None)):
    user_query = json.loads(body)["content"]
    llm_input = f"根據要求，分析需要上網查詢的資訊(內部知識不足夠)。生成需要上網查詢資訊的的關鍵字(不需要相關說明，直接回傳關鍵字，例如: 關鍵字1 關鍵字2 關鍵字3): {user_query} " 
    print(user_query)
    Google_Search_Keywords = rag.generate_gemini_response(llm_input, gemini_api_key, model_name)
    search_results = rag.search_google_custom(Google_Search_Keywords, google_search_api_key, google_cse_id, num_results=10)
    query=rag.augmented_prompt(user_query,search_results)
    gemini_output = rag.generate_gemini_response(query, gemini_api_key, model_name)

    respone={"respone":f"{gemini_output}"}
    
    return JSONResponse(respone)




app.mount("/",StaticFiles(directory="static",html=True))