import google.generativeai as genai 
from googleapiclient.discovery import build 



#生成LLM回應
def generate_gemini_response(llm_input, model_api_key, model_name):
    """
    使用 Google Gemini API 生成回應。

    Args:
        llm_input: 用戶輸入（包含問題和檢索到的資料）。
        model_api_key: Google Gemini API 金鑰。
        model_name: Gemini 模型名稱，預設是 "gemini-1.5-flash"。
    Returns:
        Gemini 生成的回應。
    """
    genai.configure(api_key=model_api_key)
    model = genai.GenerativeModel(model_name=model_name)
    try:
        response = model.generate_content(llm_input)
        return response.text
    except Exception as e:
        print(f"gemini回應發生問題: {e}")
        return None

#檢索 Retrievel (Google Search)，並回傳搜尋到的網頁前n筆資料
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
    service = build("customsearch", "v1", developerKey=google_search_api_key)   #建立搜尋服務
    try:
      response = (
          service.cse()
          .list(q=query, cx=google_cse_id, num=num_results)
          .execute()
      )
      results = response.get("items", [])
      formatted_results = []
      for item in results:
          formatted_results.append({
              "標題": item.get("title", ""),
              "摘要": item.get("snippet", "")
          })
      return formatted_results
    
    except Exception as e:
        print(f"google search發生問題: {e}")
        return []
    
#將檢索到的資料加到query
def augmented_prompt(query,search_results):
     # 建立 LLM 輸入字串
    retrieval_content = ""
    for result in search_results:
        retrieval_content += f"標題：{result['標題']}\n"
        retrieval_content += f"摘要：{result['摘要']}\n"
    prompt=f"請你做出正常的回應，不必提到你參考過哪些資料，這是使用者提問的問題:\n{query}"+f"請參考以下資料做出回應:\n{retrieval_content[:4000]}"
    return prompt