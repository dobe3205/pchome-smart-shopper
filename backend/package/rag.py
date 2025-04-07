import google.generativeai as genai 
from googleapiclient.discovery import build 
import requests
from bs4 import BeautifulSoup
import logging
import json

# 設定日誌
logger = logging.getLogger(__name__)

class RAGService:
    """
    RAG (Retrieval-Augmented Generation) 服務類
    整合了關鍵字生成、Google搜尋、網頁爬蟲和LLM回應生成功能
    """
    
    def __init__(self, gemini_api_key, google_search_api_key, google_cse_id, model_name="gemini-1.5-flash"):
        """
        初始化RAG服務
        
        Args:
            gemini_api_key: Google Gemini API金鑰
            google_search_api_key: Google Search API金鑰
            google_cse_id: Google Custom Search Engine ID
            model_name: Gemini模型名稱，預設為"gemini-1.5-flash"
        """
        self.gemini_api_key = gemini_api_key
        self.google_search_api_key = google_search_api_key
        self.google_cse_id = google_cse_id
        self.model_name = model_name
        
        # 設定Gemini API
        genai.configure(api_key=self.gemini_api_key)
        
    def create_search_keywords_prompt(self, user_query):
        """
        根據用戶query，產生關鍵字用於google search
        
        Args:
            user_query: 用戶的原始查詢
            
        Returns:
            融合提示詞的query
        """
        return f"""
                我需要你擔任關鍵字生成專家，根據用戶的購物需求生成精確的搜尋關鍵字。請保持簡潔，每次只產生1到5個最相關的關鍵字，不需要任何解釋。
                這是要用來做google搜尋的，你無須解釋任何步驟，只要在最後回傳關鍵字即可，格式(中間要空格):關鍵字1 關鍵字2 ...
                步驟1: 識別品牌 (如果有指定)
                品牌: [提取用戶提到的品牌，如ASUS、ACER、HP等]

                步驟2: 確定產品基本類別
                商品種類: [確定是筆電、平板、手機等主要類別]

                步驟3: 分析關鍵需求特徵
                需求特徵: [將用戶需求轉換為PChome常用的描述詞，如"方便攜帶"→"輕薄"、"打電動"→"電競"、"3A大作"→"電競"]

                步驟4: 提取關鍵規格參數
                規格參數: [提取數字和關鍵規格，並轉換為搜尋用格式，如"16G記憶體"→"16GB""]

                步驟5: 組合最終關鍵字（3-5個，按重要性排序）
                最終關鍵字: [品牌] [商品種類] [需求特徵] [規格參數]

                以下是範例：
                提問:比較電競筆電
                思考過程:
                步驟1: 識別品牌
                品牌: 未指定特定品牌

                步驟2: 確定產品基本類別
                商品種類: 筆電

                步驟3: 分析關鍵需求特徵
                需求特徵: 電競

                步驟4: 提取關鍵規格參數
                規格參數: 無

                步驟5: 組合最終關鍵字
                最終關鍵字: 電競 筆電

                提問: 我需要一台適合辦公室使用的電腦，預算15000元以內，主要是處理文書工作和瀏覽網頁。
                思考過程:
                步驟1: 識別品牌
                品牌: 未指定特定品牌

                步驟2: 確定產品基本類別
                商品種類: 電腦 (可細分為桌機)

                步驟3: 分析關鍵需求特徵
                需求特徵: 辦公室使用、文書處理 → 文書機 或 商用

                步驟4: 提取關鍵規格參數
                規格參數: 預算15000以內 → 不需放入關鍵字，價格可在後續篩選

                步驟5: 組合最終關鍵字
                最終關鍵字: 桌機 文書機 商用
                
                提問: 想找一台MSI的電競筆電，需要有i9處理器和RTX 4080顯卡，螢幕要有165Hz的更新率。
                思考過程:
                步驟1: 識別品牌
                品牌: MSI

                步驟2: 確定產品基本類別
                商品種類: 筆電 (電競筆電)

                步驟3: 分析關鍵需求特徵
                需求特徵: 電競 → 電競筆電

                步驟4: 提取關鍵規格參數
                規格參數: i9處理器 → i9
                        RTX 4080顯卡 → RTX4080
                        165Hz更新率 → 165Hz

                步驟5: 組合最終關鍵字
                最終關鍵字: MSI 電競筆電 i9 RTX4080 165Hz
                
                提問: 推薦一款可以遠端控制的掃地機器人，要能連接APP並能自動倒垃圾，預算10000元左右。
                步驟1: 識別品牌
                品牌: 未指定特定品牌

                步驟2: 確定產品基本類別
                商品種類: 掃地機器人

                步驟3: 分析關鍵需求特徵
                需求特徵: 遠端控制 → APP控制
                        自動倒垃圾 → 自動集塵

                步驟4: 提取關鍵規格參數
                規格參數: 預算10000左右 → 不納入關鍵字

                步驟5: 組合最終關鍵字
                最終關鍵字: 掃地機器人 APP控制 自動集塵

                提問: 我想買一台三星最新的折疊手機，需要有較大的螢幕和長效電池，支援快速充電。
                思考過程:
                步驟1: 識別品牌
                品牌: 三星 (Samsung)

                步驟2: 確定產品基本類別
                商品種類: 折疊手機

                步驟3: 分析關鍵需求特徵
                需求特徵: 較大螢幕 → 大螢幕
                        長效電池 → 大電量
                        快速充電 → 快充

                步驟4: 提取關鍵規格參數
                規格參數: 最新 → 可用型號表示，如Galaxy Z Fold

                步驟5: 組合最終關鍵字
                最終關鍵字: 三星 折疊手機 Z Fold 大電量

                提問:有沒有適合初學者使用的Canon單眼相機，想拍風景和人像，希望有好的低光源表現，預算在30000元以內。
                思考過程:
                現在，請根據以下用戶需求產生關鍵字：
                步驟1: 識別品牌
                品牌: Canon

                步驟2: 確定產品基本類別
                商品種類: 單眼相機

                步驟3: 分析關鍵需求特徵
                需求特徵: 初學者 → 入門
                        風景和人像 → 不特別納入關鍵字
                        低光源表現 → 低光

                步驟4: 提取關鍵規格參數
                規格參數: 預算30000以內 → 不納入關鍵字

                步驟5: 組合最終關鍵字
                最終關鍵字: Canon 單眼相機 入門 低光


                提問: 我想找一款Sony的降噪藍牙耳機，希望電池續航力長，可以運動時使用，預算5000元以內，喜歡黑色款式。
                步驟1: 識別品牌
                品牌: Sony

                步驟2: 確定產品基本類別
                商品種類: 藍牙耳機

                步驟3: 分析關鍵需求特徵
                需求特徵: 降噪功能 → 降噪
                        電池續航力長 → 長效電池 或 續航
                        運動時使用 → 運動耳機 + 防水
                        黑色款式 → 黑色 (較次要特徵，可考慮不納入關鍵字)

                步驟4: 提取關鍵規格參數
                規格參數: 防水功能通常需要 → IPX4或以上
                        預算5000元以內 → 不納入關鍵字

                步驟5: 組合最終關鍵字
                最終關鍵字: Sony 藍牙耳機 降噪 運動 防水

                現在請你舉一反三，根據以上規格產生關鍵字
                用戶需求: {user_query}
                """

    def get_gemini_response(self, llm_input):
        """
        調整生成回應參數，並使用 Google Gemini API 生成回應。

        Args:
            llm_input: 用戶輸入（包含問題和檢索的資料）。
            
        Returns:
            Gemini 生成的回應。
        """
        model = genai.GenerativeModel(model_name=self.model_name)
        try:
            # 設置生成參數，提高輸出品質
            generation_config = {
                "temperature": 0.2,  # softmax中logit/t
                "top_p": 0.95,       # token機率總和
                "top_k": 40,         # 前k個token
                "max_output_tokens": 4096  # 輸出最多幾個token
            }
            
            response = model.generate_content(
                llm_input,
                generation_config=generation_config  # 如有需求再做設定
            )
            return response.text  # 只取回應，其它暫且沒用到
        except Exception as e:
            logger.error(f"Gemini回應生成錯誤: {e}")
            return None

    def google_search(self, query, num_results=10):
        """
        使用 Google Custom Search API 進行搜尋。
        
        Args:
            query: 用戶的搜尋查詢。
            num_results: 返回的搜尋結果數量。
            
        Returns:
            搜尋結果的列表，每個結果包含 title、link 和 snippet。
        """
        pchome_query = f"inurl:24h.pchome.com.tw/prod {query}"  # 用inurl限制搜尋結果
        service = build("customsearch", "v1", developerKey=self.google_search_api_key)
        try:
            # 優化檢索參數
            search_params = {
                "q": pchome_query,            # 搜尋的關鍵字
                "cx": self.google_cse_id,     # key
                "num": num_results,          # 取搜尋的前幾筆資料
                "safe": "active",             # 安全搜尋，過濾不良內容
                "gl": "tw",                   # 地理位置偏好（台灣）
                "hl": "zh-TW"                 # 搜尋結果語言偏好（繁體中文）
            }
            
            logger.info(f"執行Google搜尋，關鍵字: {query}")
            response = service.cse().list(**search_params).execute()
            
            results = response.get("items", [])  # 需要的內容都在items(key)，value為array裡面是dict
            logger.info(f"搜尋返回結果數量: {len(results)}")
            
            formatted_results = []  # 把需要的東西整理出來
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

    def create_comparison_prompt(self, user_query, retrival_info=None):
        """
        產品比較提示詞設計
        
        Args:
            user_query: 用戶原始查詢
            retrival_info: 檢索的資料
            
        Returns:
            最終的產品比較提示詞
        """
        print(retrival_info)
        spec = {
            "comparison_results": {
                "best_choice": "最佳商品名稱",
                "best_value": "最高性價比商品",
                "best_quality": "最佳品質商品",
                "most_features": "功能最齊全商品"
            },
            "product_comparisons": [
                {
                    "product_name": "商品名稱",
                    "brand": "品牌名稱",
                    "price": "價格",
                    "pros": ["優點 1", "優點 2", "..."],
                    "cons": ["缺點 1", "缺點 2", "..."],
                    "key_features": ["特色 1", "特色 2", "..."],
                    "suitable_scenarios": ["適用場景 1", "適用場景 2", "..."],
                    "rating": 8.5,
                    "link": "直接從產品資訊中複製完整的購買連結，不要修改或創造連結"
                },
                {
                    "product_name": "商品名稱",
                    "brand": "品牌名稱",
                    "price": "價格",
                    "pros": ["優點 1", "優點 2", "..."],
                    "cons": ["缺點 1", "缺點 2", "..."],
                    "key_features": ["特色 1", "特色 2", "..."],
                    "suitable_scenarios": ["適用場景 1", "適用場景 2", "..."],
                    "rating": 7.8,
                    "link": "直接從產品資訊中複製完整的購買連結，不要修改或創造連結"
                }
            ],
            "analysis": "整體比較分析和建議"
        }
        
        # 創建比較產品的提示詞
        prompt = f"""
        你是專業的產品顧問，專門幫助用戶做出最佳購買決策。請用繁體中文回答並根據用戶需求和提供的產品資訊，進行全面的分析並以JSON格式回答結構如以下所示，商品的部分不只兩個，只是舉例而已，如果有超過4種產品，請至少比較4種最相關的，並把參考的產品資料中的連結填入JSON結構，特別注意商品購買連結，key使用對應的英文，內容使用繁體中文，不用附加額外訊息，也不要使用markdown格式:
        {spec}

        # 用戶需求
        {user_query}

        # 分析步驟
        身為產品分析師，我需要先了解每個產品的基本資訊。我將從以下產品資訊中提取：
        產品名稱和品牌 價格 主要規格和特點 目標用途 購買連結

        接著，我需要評估每個產品的優缺點：
        優點：哪些特性特別出色？
        缺點：有哪些明顯的不足？
        關鍵特色：最與眾不同的功能是什麼？
        適用場景：哪類用戶最適合使用此產品？

        然後，我將依據以下標準評分(1-10分)：
        整體品質 性價比 功能完整性 使用者體驗

        最後，我會判斷：
        最佳整體選擇 最佳性價比選擇 最佳品質選擇 功能最齊全選擇 提供整體分析和建議

        在提交最終JSON前，請檢查：
        從每個相關產品中提取重要資訊，包括購買連結(link)
        是否已識別每個產品的主要優缺點？
        評分是否反映了產品的實際優劣(1-10分)?
        最佳選擇是否有充分依據？
        JSON格式是否完全符合要求？
        是否包含了有用的整體分析？
        讓分析結果清晰易讀，保持客觀專業的語調，不要在回應中提及你參考了哪些資料，也不要回應不相關的產品。
        
        必須確保回傳結果是嚴格的JSON格式
        # 產品資訊
        {retrival_info}
        """
        return prompt

    def pchome_search(self, search_results):
        """
        在pchome商品搜尋google search回傳的連結，並把商品資訊整合在一起
        
        Args:
            search_results: Google搜尋結果列表
            
        Returns:
            整合後的商品資訊字串
        """
        s = ""
        for search_result in search_results:
            s += f"{self.get_pchome_product_info(search_result.get('連結'))}\n"
            
        return s

    def get_pchome_product_info(self, url):
        """
        從 PChome 商品網址提取產品資訊，並組合成文字字串
       
        Args:
            url: PChome 商品頁面的 URL
       
        Returns:
            格式化的產品資訊字串
        """
        try:
            # 取得網頁內容
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 清理資料
            # 商品名稱
            product_name_elem = soup.find('h1', {'class': 'o-prodMainName__grayDarkest--l700'})
            product_name = product_name_elem.text.strip() if product_name_elem else "無商品名稱"
           
            # 價格
            price_element = soup.find('div', {'class': 'o-prodPrice__price'})
            price = price_element.text.strip() if price_element else "無價格資訊"
           
            original_price_element = soup.find('div', {'class': 'o-prodPrice__originalPrice'})
            original_price = original_price_element.text.strip() if original_price_element else "無原始價格資訊"
           
            # 品牌
            brand_element = soup.find('span', {'class': 'o-prodMainName__colorSecondary'})
            brand = brand_element.text.strip() if brand_element else "查無品牌"
           
            # 特色
            features_list = soup.find('ul', {'class': 'c-blockCombine__list--prodSlogan'})
            features = [li.text.strip() for li in features_list.find_all('li')] if features_list else []
           
            # 規格
            specs_text = ""
            spec_divs = soup.find_all('div', {'class': 'c-blockCombine__item--prodSpecification'})
            for spec in spec_divs:
                specs_text += spec.get_text(strip=True, separator='\n') + "\n"
           
            # 規格表格
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
                f"購買連結: {url}"
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
            return result + "\n"
       
        except Exception as e:
            return f"爬取商品資訊時發生錯誤: {str(e)}"
        
    def extract_json_from_response(self, response):
        """從回應中提取JSON格式的內容
        
        Args:
            response: LLM生成的回應文字
            
        Returns:
            JSON字串，如果找不到則返回None
        """
        if "```json" in response:
            parts = response.split("```json")
            if len(parts) > 1:
                json_part = parts[1].split("```")[0].strip()
                return json_part
        return None

    def process_product_comparison(self, user_query):
        """
        處理用戶產品比較請求的完整流程，提供結構化JSON回應
        
        Args:
            user_query: 用戶的查詢字串
            
        Returns:
            tuple: (原始回應文字, 解析後的JSON字典)
                - 第一個是原始回應文字，用於儲存到資料庫
                - 第二個是解析後的JSON字典，傳給前端
        """
        try:
            # 步驟1: 生成搜尋關鍵詞
            logger.info("步驟1: 生成搜尋關鍵詞")
            keywords_prompt = self.create_search_keywords_prompt(user_query)
            search_keywords = self.get_gemini_response(keywords_prompt)
            logger.info(f"生成的搜尋關鍵詞: {search_keywords}")
            
            # 步驟2: 執行Google搜尋
            logger.info("步驟2: 執行Google搜尋")
            search_results = self.google_search(search_keywords, num_results=10)
            
            # 步驟3: 整理PChome產品資訊
            logger.info("步驟3: 整理PChome產品資訊")
            retrival_info = self.pchome_search(search_results)
            
            # 步驟4: 生成產品比較和分析
            logger.info("步驟4: 生成產品比較和分析")
            final_prompt = self.create_comparison_prompt(user_query, retrival_info)
            final_response = self.get_gemini_response(final_prompt)
            
            # 步驟5: 處理回應，提取JSON
            json_str = self.extract_json_from_response(final_response)
            
            # 解析JSON字串為Python字典
            if json_str:
                try:
                    json_data = json.loads(json_str)
                    # 返回原始回應和解析後的JSON
                    return final_response, json_data
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析錯誤: {e}")
                    # 如果JSON無法解析，返回原始回應和一個包含錯誤信息的字典
                    return final_response, {"error": "無法解析LLM回應的JSON格式", "response": final_response}
            else:
                # 如果找不到JSON，返回原始回應和一個包含原始回應的字典
                return final_response, {"response": final_response}
                
        except Exception as e:
            logger.error(f"處理產品比較時發生錯誤: {str(e)}")
            # 返回錯誤信息
            return str(e), {"error": f"處理產品比較時發生錯誤: {str(e)}"}



