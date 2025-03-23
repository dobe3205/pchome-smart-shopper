# 基於 RAG 的商品比較系統

一個使用 Retrieval-Augmented Generation (RAG) 技術的商品比較和推薦系統。系統可以根據用戶需求，通過網路搜尋不同產品的資訊，並生成產品比較分析和購買建議。

## 系統架構

- **前端**: 簡單的 HTML 頁面，用於用戶輸入商品需求和展示結果
- **後端**: FastAPI 應用，處理用戶請求和協調 RAG 流程
- **RAG 引擎**: 使用 Google Gemini API 作為 LLM，結合 Google Custom Search API 進行外部知識檢索

##  RAG 處理流程

1. **關鍵詞生成**: 分析用戶需求，生成優化的搜尋關鍵詞
2. **資訊檢索**: 使用生成的關鍵詞通過 Google 搜尋獲取相關產品資訊
3. **產品資訊提取**: 從搜尋結果中提取並結構化產品資訊
4. **產品比較分析**: 根據用戶需求和結構化產品資訊生成全面的比較分析

## 基於研究的提示詞工程

- **Chain-of-Thought 方法**: 透過結構化思維流程提高比較分析的品質
- **反思機制**: 系統會審視自己的分析過程，確保結果的全面性和客觀性
- **情境化分析**: 針對特定使用場景提供更相關的產品推薦

## 安裝與配置

### 前置需求
- Python 3.12.7
- Docker (可選，用於容器化部署)

### API 金鑰註冊
- 請至 [Google AI Studio](https://aistudio.google.com/apikey) 註冊 Gemini API Key
- 請至 [Google Custom Search API](https://developers.google.com/custom-search/v1/overview?hl=zh-tw) 註冊 Google Search API
- 請至 [Google Programmable Search Engine](https://programmablesearchengine.google.com/controlpanel/create) 建立並獲取 CSE ID

### 環境設定
1. 克隆專案或下載原始碼
2. 在 `/app/.env` 中設定您的 API 金鑰：
   ```
   gemini_api_key="YOUR_GEMINI_API_KEY" 
   google_search_api_key="YOUR_GOOGLE_SEARCH_API_KEY"
   google_cse_id ="YOUR_GOOGLE_CSE_ID"
   model_name="gemini-1.5-flash"
   ```

## 運行方式

### 使用 Docker
```bash
# 建立 Docker 映像
docker build -t ragimage .

# 運行容器
docker run -p 8000:8000 ragimage
```

### 不使用 Docker
```bash
# 安裝必要套件
pip install -r requirements.txt

# 運行網頁
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 使用系統
1. 開啟瀏覽器訪問 http://localhost:8000/
2. 在輸入框中輸入您的商品需求，例如：「我想找一款適合遊戲的筆記型電腦，預算在3萬元以內，需要有好的散熱和獨立顯卡」
3. 點擊「送出」按鈕，系統將開始處理您的請求
4. 稍等片刻，系統將返回包含產品比較表、優缺點分析和個性化推薦的結果


