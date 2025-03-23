import google.generativeai as genai 
from googleapiclient.discovery import build 
import logging

# 設定日誌
logger = logging.getLogger(__name__)

def create_search_keywords_prompt(user_query):
    """
    根據用戶query，產生關鍵字用於google search
    Args:
        user_query: 用戶的原始查詢
        
    Returns:
        融合提示詞的query
    """
    return f"""你是電商產品專家。根據以下用戶需求，分析並生成最有效的搜尋關鍵字組合。
            用戶需求: {user_query}
            請分析:1. 產品類型與核心功能 2. 規格或特性要求 3. 用戶比較的特徵(價格、性能、品牌等)
            輸出5組精確的搜尋關鍵字組合，每組用於搜尋一個可能的相關產品。
            格式: 關鍵字1 關鍵字2 關鍵字3 關鍵字4 關鍵字5
            無需解釋，僅輸出關鍵字組合，每組一行。
            """

def generate_gemini_response(llm_input, model_api_key, model_name):
    """
    調整生成回應參數，並使用 Google Gemini API 生成回應。

    Args:
        llm_input: 用戶輸入（包含問題和檢索的資料）。
        model_api_key: Google Gemini API 金鑰。
        model_name: Gemini 模型名稱，預設是 "gemini-1.5-flash"。
    Returns:
        Gemini 生成的回應。
    """
    genai.configure(api_key=model_api_key)
    model = genai.GenerativeModel(model_name=model_name)
    try:
        # 設置生成參數，提高輸出品質
        generation_config = {
            "temperature": 0.2, #softmax中logit/t
            "top_p": 0.95,      #token機率總和
            "top_k": 40,        #前k個token
            "max_output_tokens": 4096   #輸出最多幾個token
        }
        
        response = model.generate_content(
            llm_input,
            generation_config=generation_config
        )
        return response.text    #只取回應，其它暫且沒用到
    except Exception as e:
        logger.error(f"Gemini回應生成錯誤: {e}")
        return None

def search_google_custom(query, google_search_api_key, google_cse_id, num_results):
    """
    使用 Google Custom Search API 進行搜尋。
    Args:
        query: 用戶的搜尋查詢。
        google_search_api_key: Google API 金鑰。
        google_cse_id: Google Custom Search Engine 的 ID。
        num_results: 返回的搜尋結果數量。
    Returns:
        搜尋結果的列表，每個結果包含 title、link 和 snippet。
    """
    service = build("customsearch", "v1", developerKey=google_search_api_key)
    try:
        # 優化檢索參數
        search_params = {
            "q": query,             #搜尋的關鍵字
            "cx": google_cse_id,    #key
            "num": num_results,     #取搜尋的前幾筆資料
            "safe": "active",       #安全搜尋，過濾不良內容
            "gl": "tw",             #地理位置偏好（台灣）
            "hl": "zh-TW"           #搜尋結果語言偏好（繁體中文）
        }
        
        logger.info(f"執行Google搜尋，關鍵詞: {query}")
        response = service.cse().list(**search_params).execute()
        
        results = response.get("items", []) #需要的內容都在items(key)，value為array裡面是dict
        logger.info(f"搜尋返回結果數量: {len(results)}")
        
        formatted_results = []  #把需要的東西整理出來
        for item in results:
            formatted_results.append({
                "標題": item.get("title", ""),
                "連結": item.get("link", ""),
                "摘要": item.get("snippet", ""),
                "來源": item.get("displayLink", "")
            })
        return formatted_results
    
    except Exception as e:
        logger.error(f"Google搜尋發生錯誤: {e}")
        return []
    
def extract_product_info(search_results, gemini_api_key, model_name):
    """
    設計整理產品特性的提示詞，處理google search得到的檢索資料，整理出產品特點
    Args:
        search_results: 搜尋返回的產品資訊列表
        gemini_api_key: Gemini API金鑰
        model_name: 使用的模型名稱
        
    Returns:
        整理過的檢索資料(JSON格式)
    """
    # 將搜尋結果格式化為文本
    search_content = ""
    for i, result in enumerate(search_results, 1):
        search_content += f"來源 {i}:\n"
        search_content += f"標題: {result['標題']}\n"
        search_content += f"摘要: {result['摘要']}\n"
        if '連結' in result:
            search_content += f"連結: {result['連結']}\n"
        if '來源' in result:
            search_content += f"來源網站: {result['來源']}\n"
        search_content += "\n"
    
    # 創建產品提示詞
    extraction_prompt = f"""
    你是產品分析專家。請從以下搜尋結果中識別並整理所有的產品資訊。
    搜尋結果:
    {search_content}

    請執行以下步驟:
    1. 首先思考搜尋結果中提到的是哪些產品 (品牌和型號)
    2. 對於每個識別出的產品，整理以下資訊:
    - 完整產品名稱
    - 品牌
    - 型號
    - 價格(如果提到)
    - 主要技術規格(如處理器、記憶體、儲存等)
    - 關鍵特性和賣點
    - 評價要點(如果提到)

    3. 將資訊以JSON格式輸出:
    {{"products": [
    {{"name": "完整產品名稱", "brand": "品牌", "model": "型號", "price": "價格", "specs": ["規格1", "規格2"], "features": ["特性1", "特性2"], "ratings": "評價"}},
    {{...另一產品...}}
    ]}}

    僅輸出JSON格式，不要有其它文字。如果某個欄位無法確定，使用空字符串""。
    """
    
    # 使用Gemini提取產品資訊
    logger.info("開始整理產品資訊")
    structured_data = generate_gemini_response(extraction_prompt, gemini_api_key, model_name)
    logger.info("整理產品資訊完成")
    
    return structured_data


def final_comparison_prompt(user_query, search_results, structured_data=None):
    """
    產品比較提示詞設計
    Args:
        user_query: 用戶原始查詢
        search_results: 搜尋結果列表
        structured_data: 結構化的產品資訊(可選)
        
    Returns:
        最終的產品比較提示詞
    """
    # 如果無法整理出產品資訊，使用原始google search結果
    if not structured_data or structured_data == "None":
        logger.warning("未提整理好的資料，使用原始搜尋結果")
        retrieval_content = ""
        for i, result in enumerate(search_results, 1):
            retrieval_content += f"資料來源 {i}:\n"
            retrieval_content += f"標題：{result['標題']}\n"
            retrieval_content += f"摘要：{result['摘要']}\n\n"
        context = retrieval_content
    else:
        context = structured_data
    
    # 創建比較產品的提示詞
    prompt = f"""
    你是專業的產品比較顧問，專門幫助用戶做出最佳購買決策。請根據用戶需求和提供的產品資訊，進行全面、客觀的比較分析。

    # 用戶需求
    {user_query}

    # 產品資訊
    {context}

    # 分析步驟
    ## 步驟1: 需求分析
    分析用戶的核心需求、優先考量因素和可能的使用場景。思考用戶可能沒有明確表達但重要的隱含需求。

    ## 步驟2: 產品資訊整理
    從提供的資料中識別相關產品，並整理關鍵產品資訊。確保資訊的完整性和準確性。

    ## 步驟3: 建立比較框架
    建立合適的比較框架，包括:
    - 核心功能比較
    - 性價比分析
    - 使用體驗
    - 適用場景

    ## 步驟4: 反思與校正
    檢查比較過程是否存在偏見、資訊不全或邏輯漏洞。如有必要，調整分析框架。

    # 輸出格式
    請提供以下內容:

    1. 產品比較表格 - 包含所有找到的相關產品，列出品牌、型號、價格和關鍵規格

    2. 產品優缺點分析 - 對每個產品的優勢和局限性進行分析，特別關注用戶的關鍵需求

    3. 個性化推薦
    - 整體最佳選擇
    - 最佳性價比選擇
    - 特定用途的最佳選擇(如適用)
    - 如果用戶有特殊需求，提供最符合這些需求的選擇

    4. 購買建議與注意事項
    - 購買時應考慮的重要因素
    - 其他備選方案(如有)
    - 未來發展趨勢考量(如適用)

    請使用表格、項目符號等結構化格式呈現資訊，使分析結果清晰易讀。保持客觀專業的語調，不要在回應中提及你參考了哪些資料，也不要說你的資訊不夠。
    """
    return prompt


# 舊版
def augmented_prompt(query, search_results):
    """
    將檢索到的資料加到查詢中 (舊版本，保留以向後兼容)
    
    建議使用新的final_comparison_prompt函數替代
    
    Args:
        query: 用戶查詢
        search_results: 搜尋結果
        
    Returns:
        增強的提示詞
    """
    logger.warning("使用舊版augmented_prompt函數，建議升級到final_comparison_prompt")
    # 建立 LLM 輸入字串
    retrieval_content = ""
    for result in search_results:
        retrieval_content += f"標題：{result['標題']}\n"
        retrieval_content += f"摘要：{result['摘要']}\n"
    prompt = f"請你做出正常的回應，不必提到你參考過哪些資料，這是使用者提問的問題:\n{query}"+f"請參考以下資料做出回應:\n{retrieval_content[:4000]}"
    return prompt