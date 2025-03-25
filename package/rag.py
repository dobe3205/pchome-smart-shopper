import google.generativeai as genai 
from googleapiclient.discovery import build 
import requests
from bs4 import BeautifulSoup
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
    return f"""
            我需要你擔任關鍵字生成專家，根據用戶的購物需求生成精確的搜尋關鍵字。請保持簡潔，每次只產生1到2個最相關的關鍵字，不需要任何解釋。

            以下是範例：

            用戶需求: 我想找一台價格在5萬以內，輕薄但性能還不錯的筆電
            關鍵字: 筆電 輕薄

            用戶需求: 推薦一款拍照效果好的手機，預算1萬5以內
            關鍵字: 手機 拍照

            用戶需求: 我需要一個可以防塵防水的手錶，適合運動時佩戴
            關鍵字: 運動手錶 防水

            用戶需求: 幫我找一個時尚的女用側背包，皮質的比較好
            關鍵字: 側背包 女用

            用戶需求: 想買一個能煮多種料理的電子鍋，最好是小型的
            關鍵字: 多功能電子鍋 小型

            用戶需求: 幫我找一款日系品牌的咖啡機，預算5000元以內
            關鍵字: 日系咖啡機 

            用戶需求: 比較不同牌子的藍芽耳機，想要降噪效果好的
            關鍵字: 藍芽耳機 降噪

            用戶需求: 尋找適合初學者的單眼相機，價格不要太貴
            關鍵字: 單眼相機 平價

            用戶需求: 我想要一台可以語音控制的智慧家電，例如電視或是音響
            關鍵字: 智慧家電 語音

            現在，請根據以下用戶需求產生關鍵字：
            用戶需求: {user_query}
            """

def gemini_response(llm_input, model_api_key, model_name):
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

def google_search(query, google_search_api_key, google_cse_id, num_results):
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
    pchome_query = f"inurl:24h.pchome.com.tw/prod {query}" #限制搜尋結果
    service = build("customsearch", "v1", developerKey=google_search_api_key)
    try:
        # 優化檢索參數
        search_params = {
            "q": pchome_query,             #搜尋的關鍵字
            "cx": google_cse_id,    #key
            "num": num_results,     #取搜尋的前幾筆資料
            "safe": "active",       #安全搜尋，過濾不良內容
            "gl": "tw",             #地理位置偏好（台灣）
            "hl": "zh-TW"           #搜尋結果語言偏好（繁體中文）
        }
        
        logger.info(f"執行Google搜尋，關鍵字: {query}")
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


def final_comparison_prompt(user_query, retrival_info=None):
    """
    產品比較提示詞設計
    Args:
        user_query: 用戶原始查詢
        retrival_info:檢索的資料
        
    Returns:
        最終的產品比較提示詞
    """
    spec={
        "comparison_results": {
            "best_choice": "Product Name",
            "best_value": "Product Name",
            "best_quality": "Product Name",
            "most_features": "Product Name"
        },
        "product_comparisons": [
            {
                "product_name": "Product A",
                "brand": "Brand Name",
                "price": "Price",
                "pros": ["Pro 1", "Pro 2", "..."],
                "cons": ["Con 1", "Con 2", "..."],
                "key_features": ["Feature 1", "Feature 2", "..."],
                "suitable_scenarios": ["Scenario 1", "Scenario 2", "..."],
                "rating": 8.5
            },
            {
                "product_name": "Product B",
                "brand": "Brand Name",
                "price": "Price",
                "pros": ["Pro 1", "Pro 2", "..."],
                "cons": ["Con 1", "Con 2", "..."],
                "key_features": ["Feature 1", "Feature 2", "..."],
                "suitable_scenarios": ["Scenario 1", "Scenario 2", "..."],
                "rating": 7.8
            }
            ],
        "analysis": "Overall comparison analysis and recommendations"
        }
    # 創建比較產品的提示詞
    prompt = f"""
    你是專業的產品顧問，專門幫助用戶做出最佳購買決策。請根據用戶需求和提供的產品資訊，進行全面的分析並以JSON格式回答結構如以下所示，回答請跟結構一模一樣，不用附加額外訊息，也不要使用markdown格式:
    {spec}

    # 用戶需求
    {user_query}

    # 產品資訊
    {retrival_info}

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

    # 輸出格式
    請提供以下內容:

    1. 比較找到的相關產品，列出品牌、型號、價格、規格以及購買連結

    2. 產品優缺點分析 - 對每個產品的優點和缺點進行分析，特別關注用戶的需求

    3. 個性化推薦
    - 整體最佳選擇
    - 最佳性價比選擇
    - 特定用途的最佳選擇(如適用)
    - 如果用戶有特殊需求，提供最符合這些需求的選擇

    4. 購買建議與注意事項
    - 購買時應考慮的重要因素
    - 其他備選方案(如有)
    - 未來發展趨勢考量(如適用)

    讓分析結果清晰易讀，保持客觀專業的語調，不要在回應中提及你參考了哪些資料，也不要說你的資訊不足，不用總結。
    """
    return prompt


#在pchome商品搜尋google search回傳的連結，並把商品資訊整合再一起
def pchome_search(search_results):
    s=""
    for search_result in search_results:
        s+=f"{get_pchome_product_info(search_result.get("連結"))}\n"
        
    return s

#爬取pchome資料
def get_pchome_product_info(url):
   """
   從 PChome 商品網址提取產品資訊，並組合成文字字串
   
   參數:
   url (str): PChome 商品頁面的 URL
   
   返回:
   str: 格式化的產品資訊字串
   """
   try:
       # 取得網頁內容
       response = requests.get(url)
       soup = BeautifulSoup(response.text, 'html.parser')
       #清理資料
       #商品名稱
       product_name_elem = soup.find('h1', {'class': 'o-prodMainName__grayDarkest--l700'})
       product_name = product_name_elem.text.strip() if product_name_elem else "無商品名稱"
       
       #價格
       price_element = soup.find('div', {'class': 'o-prodPrice__price'})
       price = price_element.text.strip() if price_element else "無價格資訊"
       
       original_price_element = soup.find('div', {'class': 'o-prodPrice__originalPrice'})
       original_price = original_price_element.text.strip() if original_price_element else "無原始價格資訊"
       
       #品牌
       brand_element = soup.find('span', {'class': 'o-prodMainName__colorSecondary'})
       brand = brand_element.text.strip() if brand_element else "查無品牌"
       
       #特色
       features_list = soup.find('ul', {'class': 'c-blockCombine__list--prodSlogan'})
       features = [li.text.strip() for li in features_list.find_all('li')] if features_list else []
       
       #規格
       specs_text = ""
       spec_divs = soup.find_all('div', {'class': 'c-blockCombine__item--prodSpecification'})
       for spec in spec_divs:
           specs_text += spec.get_text(strip=True, separator='\n') + "\n"
       
       #規格表格
       spec_tables = soup.find_all('table', {'class': 'c-tableGrid--prodSpec'})
       specs = {}
       
       for table in spec_tables:
           rows = table.find_all('tr')
           
           for row in rows:
               header = row.find('th')
               data = row.find('div', {'class': 'c-tableGrid__htmlText'})
               
               if header and data:
                   key = header.get_text(strip=True)
                   value = data.get_text(strip=True)
                   
                   # 處理重複的key
                   if key in specs:
                       # 如果key已存在，轉換為list或加到list
                       if isinstance(specs[key], list):
                           specs[key].append(value)
                       else:
                           specs[key] = [specs[key], value]
                   else:
                       specs[key] = value
       
       # 組合所有資訊
       info_parts = [
           f"商品名稱: {product_name}",
           f"品牌: {brand}",
           f"售價: {price}",
           f"購買連結:{url}"
       ]
       
       if original_price:
           info_parts.append(f"原價: {original_price}")
       
       if features:
           info_parts.append("商品特點:")
           for feature in features:
               info_parts.append(f"- {feature}")
       
       if specs:
           info_parts.append("商品規格:")
           for key, value in specs.items():
               if isinstance(value, list):
                   info_parts.append(f"{key}: {', '.join(value)}")
               else:
                   info_parts.append(f"{key}: {value}")
       
       if specs_text:
           info_parts.append("其它規格說明:")
           info_parts.append(specs_text)
       
       # 合併所有部分為一個字串
       result = "\n".join(info_parts)
       return result+"\n"
   
   except Exception as e:
       return f"爬取商品資訊時發生錯誤: {str(e)}"
   

