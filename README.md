# pchome智能助手

一個使用RAG技術的商品比較系統。系統可以根據用戶需求，通過網路搜尋最新的產品資訊，並讓LLM生成產品比較分析和購買建議。

## 安裝與配置

### 前置需求
- Docker 

### API 金鑰註冊
- 請至 [Google AI Studio](https://aistudio.google.com/apikey) 註冊 Gemini API Key
- 請至 [Google Custom Search API](https://developers.google.com/custom-search/v1/overview?hl=zh-tw) 註冊 Google Search API
- 請至 [Google Programmable Search Engine](https://programmablesearchengine.google.com/controlpanel/create) 建立並獲取 CSE ID

### 環境設定
1. clone專案或下載原始碼
2. 在 `backend/app/` 中建立.env檔案
3. 在 `backend/app/.env` 中設定3組 API 金鑰以及自訂的model_name(Gemini)、secret_key(可為任意字串)：
   ```
   gemini_api_key="YOUR_GEMINI_API_KEY" 
   google_search_api_key="YOUR_GOOGLE_SEARCH_API_KEY"
   google_cse_id ="YOUR_GOOGLE_CSE_ID"
   model_name="gemini-2.0-flash"
   secret_key="jwtsecretkey"
   ```

## 運行方式

### 使用 Docker
```bash
# 構建所有容器
docker-compose build

# 啟動所有容器
docker-compose up -d

# 停止所有容器
docker-compose down

```

### 使用系統
1. 開啟瀏覽器訪問 http://localhost
2. 註冊或登入系統
3. 在輸入框中輸入您的商品需求，例如：「我想找一款適合遊戲的筆記型電腦，預算在3萬元以內，需要有好的散熱和獨立顯卡」
4. 點擊「送出」按鈕，系統將開始處理您的請求
5. 稍等片刻，系統將返回包含產品比較表、優缺點分析和總結

## Contributors
- 前端:sm29729443(sm29729443@gmail.com)
- 後端和RAG:dobe3205(3205hh@gmail.com)
