# 基於 RAG 的商品比較系統

一個使用 Retrieval-Augmented Generation (RAG) 技術的商品比較和推薦系統。系統可以根據用戶需求，通過網路搜尋不同產品的資訊，並生成產品比較分析和購買建議。

## 安裝與配置

### 前置需求
- Python 3.12.7
- Docker (可選，用於容器化部署)

### API 金鑰註冊
- 請至 [Google AI Studio](https://aistudio.google.com/apikey) 註冊 Gemini API Key
- 請至 [Google Custom Search API](https://developers.google.com/custom-search/v1/overview?hl=zh-tw) 註冊 Google Search API
- 請至 [Google Programmable Search Engine](https://programmablesearchengine.google.com/controlpanel/create) 建立並獲取 CSE ID

### 環境設定
1. clone專案或下載原始碼
2. 在 `/app/.env` 中設定您的 API 金鑰：
   ```
   gemini_api_key="YOUR_GEMINI_API_KEY" 
   google_search_api_key="YOUR_GOOGLE_SEARCH_API_KEY"
   google_cse_id ="YOUR_GOOGLE_CSE_ID"
   model_name="gemini-1.5-flash"
   secret_key="secret_key"
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
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 使用系統
1. 開啟瀏覽器訪問 http://localhost:8000/
2. 在輸入框中輸入您的商品需求，例如：「我想找一款適合遊戲的筆記型電腦，預算在3萬元以內，需要有好的散熱和獨立顯卡」
3. 點擊「送出」按鈕，系統將開始處理您的請求
4. 稍等片刻，系統將返回包含產品比較表、優缺點分析和個性化推薦的結果


